using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameInput;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// The steam dash, learnt from the <see cref="MechArmy.Items.CogpunkerManual"/> (user-set 2026-10-28; one manual per
	/// character, saved with the player as <see cref="SaveKey"/>). Reading it also adds <see cref="ManualSteamMax"/> to the
	/// steam tank for good (<see cref="SteamPlayer.SteamMaxInnate"/>).
	/// <list type="bullet">
	/// <item><b>Input:</b> the <see cref="SteamDashSystem.Keybind"/> (default F; towards the held direction, or the way the
	/// player faces), or a double tap left/right like vanilla's dash accessories when no other dash is equipped
	/// (ExampleMod 1.4.4 <c>ExampleDashPlayer</c>: <c>doubleTapCardinalTimer</c> read in <see cref="ResetEffects"/>, no dash
	/// with a vanilla dash, the Solar set or a mount).</item>
	/// <item><b>Cost:</b> <see cref="SteamCost"/> steam (flat: the Polished set's discount is for weapons), then
	/// <see cref="CooldownTicks"/> (4 s) before the next. Not enough steam: no dash, a dry click; never an overheat.</item>
	/// <item><b>The dash:</b> <see cref="DashSpeed"/> px/tick for <see cref="DashTicks"/> ticks, flat (gravity held off, so
	/// it crosses a gap), then it slows to a run. Projectiles pass through the player for the dash and
	/// <see cref="ProjectileGraceTicks"/> after it (<see cref="CanBeHitByProjectile"/>). Bodies don't: touching an enemy
	/// still hurts and knocks the player back, and the hit ends the dash so the knockback lands (<see cref="OnHitByNPC"/>).</item>
	/// <item><b>Looks:</b> a ring of steam and brass sparks where it starts, vanilla's afterimage trail
	/// (<c>armorEffectDrawShadowEOCShield</c>, as ExampleDashPlayer does), steam puffs streaming behind, a hiss and a whoosh;
	/// a small chime and puff when it is ready again.</item>
	/// </list>
	/// <para>D2: the owner decides and moves its own player; a <see cref="SteamDashPacket"/> (player, direction) tells
	/// everyone else, who replay only the looks. Hostile projectiles are checked on the hit player's own client
	/// (decompiled <c>Projectile.Damage</c>), so the i-frames need no sync. D1: counters only; effects client-side.</para>
	/// </summary>
	public sealed class SteamDashPlayer : ModPlayer
	{
		public const string SaveKey = "CogpunkerManual";
		public const int ManualSteamMax = 25;          // 20, +5 (user, 2026-11-26: "increase amount of max steam that all max steam increasing itens give in 5 points")
		public const int SteamCost = 15;
		public const int CooldownTicks = 240;
		public const int DashTicks = 12;
		public const float DashSpeed = 15f;               // vanilla: Tabi 16.9, Shield of Cthulhu 14.5 (decompiled Player.DashMovement)
		public const float EndSpeedFactor = 0.55f;        // the speed it keeps when the burst ends
		public const int ProjectileGraceTicks = 6;
		public const int DoubleTapWindow = 15;            // ticks (ExampleDashPlayer)
		private const int TapRight = 2, TapLeft = 3;      // doubleTapCardinalTimer indices

		/// <summary>This character has read a Cogpunker Manual (one per character).</summary>
		public bool HasManual;

		/// <summary>Ticks left in the dash (every client: drives the looks; the owner also moves).</summary>
		public int DashTimer { get; private set; }
		public int DashDirection { get; private set; } = 1;
		public int Cooldown { get; private set; }

		private int graceTimer;
		private int clickTimer;
		private int tapDirection;
		private bool keyPressed;

		public override void SaveData(TagCompound tag) {
			if (HasManual) {
				tag[SaveKey] = true;
			}
		}

		public override void LoadData(TagCompound tag) {
			HasManual = tag.GetBool(SaveKey);
		}

		public override void ResetEffects() {
			tapDirection = 0;
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			if (Player.controlRight && Player.releaseRight && Player.doubleTapCardinalTimer[TapRight] < DoubleTapWindow) {
				tapDirection = 1;
			}
			else if (Player.controlLeft && Player.releaseLeft && Player.doubleTapCardinalTimer[TapLeft] < DoubleTapWindow) {
				tapDirection = -1;
			}
		}

		public override void ProcessTriggers(TriggersSet triggersSet) {
			if (SteamDashSystem.Keybind?.JustPressed == true) {
				keyPressed = true;
			}
		}

		public override void PostUpdateEquips() {
			if (HasManual) {
				Player.GetModPlayer<SteamPlayer>().SteamMaxInnate += ManualSteamMax;
			}
		}

		public override void PreUpdateMovement() {
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			bool wantKey = keyPressed;
			keyPressed = false;
			if (DashTimer > 0) {
				Player.velocity.X = DashDirection * DashSpeed;
				Player.velocity.Y = 0f;                      // a flat burst: it carries over a gap
				Player.fallStart = (int)(Player.position.Y / 16f);
				return;
			}
			if (clickTimer > 0) {
				clickTimer--;
			}
			if (!HasManual || Cooldown > 0 || clickTimer > 0 || Player.dead || Player.CCed || Player.mount.Active || Player.pulley || Player.grappling[0] >= 0) {
				return;
			}
			int dir = 0;
			if (wantKey) {
				dir = Player.controlRight ? 1 : (Player.controlLeft ? -1 : Player.direction);
			}
			else if (tapDirection != 0 && Player.dashType == 0 && !Player.setSolar) {
				dir = tapDirection;                          // vanilla-style double tap, only without a vanilla dash
			}
			if (dir == 0) {
				return;
			}
			SteamPlayer steam = Player.GetModPlayer<SteamPlayer>();
			if (steam.Overheated || !steam.TrySpendFlat(SteamCost)) {
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = -0.6f }, Player.Center);   // a dry click: not enough steam
				}
				clickTimer = 20;                             // no click spam
				return;
			}
			StartDash(dir);
			Player.velocity.X = dir * DashSpeed;
			Player.velocity.Y = 0f;
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<SteamDashPacket>().Send(Player.whoAmI, dir);
			}
		}

		/// <summary>Every side: a dash starts (the owner's own, or one reported by a <see cref="SteamDashPacket"/>).</summary>
		internal void StartDash(int dir) {
			DashDirection = dir >= 0 ? 1 : -1;
			DashTimer = DashTicks;
			graceTimer = DashTicks + ProjectileGraceTicks;
			Cooldown = CooldownTicks;
			Player.direction = DashDirection;
			if (!Main.dedServ) {
				BurstEffects();
			}
		}

		public override void PostUpdate() {
			if (DashTimer > 0) {
				DashTimer--;
				if (!Main.dedServ) {
					TrailEffects();
				}
				if (DashTimer == 0 && Player.whoAmI == Main.myPlayer) {
					Player.velocity.X *= EndSpeedFactor;
				}
			}
			if (graceTimer > 0) {
				graceTimer--;
			}
			if (Cooldown > 0) {
				Cooldown--;
				if (Cooldown == 0 && HasManual && Player.whoAmI == Main.myPlayer && !Main.dedServ && !Player.dead) {
					ReadyEffects();
				}
			}
		}

		public override bool CanBeHitByProjectile(Projectile proj) {
			return graceTimer <= 0;
		}

		public override void OnHitByNPC(NPC npc, Player.HurtInfo hurtInfo) {
			DashTimer = 0;                                   // it hit a body: the knockback takes over
		}

		public override void UpdateDead() {
			DashTimer = 0;
			graceTimer = 0;
		}

		public override void FrameEffects() {
			if (DashTimer > 0) {
				Player.armorEffectDrawShadowEOCShield = true;   // vanilla's afterimage trail (ExampleDashPlayer)
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Looks (clients)
		// ------------------------------------------------------------------------------------------------------------

		private static readonly Color SteamWhite = new(238, 241, 243);

		private void BurstEffects() {
			SoundEngine.PlaySound(SoundID.Item34 with { Pitch = 0.2f, Volume = 0.8f }, Player.Center);           // the valve
			SoundEngine.PlaySound(SoundID.DD2_SonicBoomBladeSlash with { Pitch = 0.4f, Volume = 0.6f }, Player.Center);
			for (int i = 0; i < 18; i++) {                   // a ring of steam where it kicked off
				if (SafeSpawn.TryNewDust(Player.Center - new Vector2(4f), 8, 8, DustID.Smoke, out Dust d, 0f, 0f, 90, SteamWhite, 1.5f)) {
					d.velocity = (MathHelper.TwoPi * i / 18f).ToRotationVector2() * 3.2f - new Vector2(DashDirection * 2.5f, 0f);
					d.noGravity = true;
				}
			}
			for (int i = 0; i < 6; i++) {                    // brass sparks off the boiler
				if (SafeSpawn.TryNewDust(Player.Center - new Vector2(6f), 12, 12, DustID.GoldCoin, out Dust s, -DashDirection * 3f, -1f)) {
					s.noGravity = true;
					s.scale = 0.8f;
				}
			}
		}

		private void TrailEffects() {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			Vector2 back = new(Player.Center.X - DashDirection * Player.width * 0.5f, Player.position.Y + 6f);
			for (int i = 0; i < 2; i++) {
				if (SafeSpawn.TryNewDust(back, 4, Player.height - 12, DustID.Smoke, out Dust d, 0f, 0f, 110, SteamWhite, 1.3f)) {
					d.velocity = new Vector2(-DashDirection * Main.rand.NextFloat(1f, 3f), Main.rand.NextFloat(-0.6f, 0.2f));
					d.noGravity = true;
				}
			}
		}

		private void ReadyEffects() {
			SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = 0.5f, Volume = 0.5f }, Player.Center);
			for (int i = 0; i < 5; i++) {
				if (SafeSpawn.TryNewDust(Player.position + new Vector2(0f, Player.height - 8f), Player.width, 8, DustID.Smoke, out Dust d, 0f, -1.2f, 120, SteamWhite, 0.9f)) {
					d.noGravity = true;
				}
			}
		}
	}
}
