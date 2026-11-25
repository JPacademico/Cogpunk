using System;
using Cogpunk.Content.Bosses.Fungimancer.NPCs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Fungimancer.Polymorph
{
	/// <summary>
	/// Polymorphed (user, 2026-11-25: the Fungimancer's burp "polymorphs the player hit into a toadstool for 2.5 seconds (cant
	/// attack only jump and move) and makes so it can be damaged by other players while polymorphed"): the player is a Toadstool
	/// (<see cref="PolymorphDrawLayer"/>: the Toadstool's own frames, picked from the player's motion), can walk and jump but
	/// uses no items, no hooks, no mounts and no wings or rocket boots (<see cref="PolymorphPlayer"/>), and other players' hits
	/// land on it whether or not PvP is on (<see cref="PolymorphPvP"/>). A debuff the Nurse can't remove.
	/// <para>D2: a buff on the hit player (vanilla syncs its buffs), so every client draws the toad and every attacker's client
	/// sees whom it may hit.</para>
	/// </summary>
	public class Polymorphed : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			player.GetModPlayer<PolymorphPlayer>().Toad = true;
		}
	}

	/// <summary>Shell-Shocked (user, 2026-11-25: the rainbow mushroom's blast is "stunning the players for 1.5 seconds"): the
	/// player can't move or act (<see cref="PolymorphPlayer"/>), stars circle its head. A debuff the Nurse can't remove.</summary>
	public class ShellShocked : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			player.GetModPlayer<PolymorphPlayer>().Stunned = true;
		}
	}

	/// <summary>What the two debuffs do to a player (every side reads the synced buffs; the controls are the owner's).</summary>
	public sealed class PolymorphPlayer : ModPlayer
	{
		public bool Toad, Stunned;
		private bool wasToad;
		private int toadPhase, toadTimer;                           // the toad's own frame clock (visual)

		public override void ResetEffects() {
			Toad = false;
			Stunned = false;
		}

		public override void SetControls() {
			if (!Toad && !Stunned) {
				return;
			}
			Player.controlUseItem = Player.controlUseTile = Player.controlHook = Player.controlMount = false;
			Player.controlQuickHeal = Player.controlQuickMana = Player.controlThrow = Player.controlSmart = false;
			Player.controlTorch = false;
			if (Stunned) {                                           // shell-shocked: nothing at all
				Player.controlLeft = Player.controlRight = Player.controlUp = Player.controlDown = Player.controlJump = false;
			}
		}

		public override void PostUpdateEquips() {
			if (!Toad && !Stunned) {
				return;
			}
			Player.noItems = true;
			Player.noBuilding = true;
			if (Toad) {
				Player.wingTimeMax = 0;                              // "only jump and move": no wings, no rocket boots
				Player.wingTime = 0f;
				Player.rocketTimeMax = 0;
				Player.rocketTime = 0;
				Player.rocketBoots = 0;
			}
		}

		public override void PreUpdateMovement() {
			if (Stunned) {
				Player.velocity.X *= 0.8f;
			}
		}

		public override void PreUpdate() {
			if (Player.whoAmI == Main.myPlayer && (Toad || Stunned)) {
				if (Player.mount.Active) {
					Player.mount.Dismount(Player);
				}
				Player.RemoveAllGrapplingHooks();
			}
		}

		public override void PostUpdate() {
			if (Toad != wasToad) {
				wasToad = Toad;
				Puff();
			}
			if (Toad) {
				TickToadFrame();
			}
			if (Stunned && !Main.dedServ && Main.GameUpdateCount % 6 == 0 && CogpunkClientConfig.RollEffect()) {
				float a = Main.GameUpdateCount * 0.25f;
				Vector2 at = Player.Top + new Vector2(MathF.Cos(a) * 14f, -6f + MathF.Sin(a) * 4f);
				if (SafeSpawn.TryNewDust(at, 2, 2, DustID.YellowStarDust, out Dust d)) {
					d.noGravity = true;
					d.velocity = Vector2.Zero;
					d.scale = 0.9f;
				}
			}
		}

		/// <summary>The toad's frame from the player's motion: sitting, leaping (rising), in the air, falling, landing.</summary>
		private void TickToadFrame() {
			bool grounded = Player.velocity.Y == 0f;
			int phase = grounded ? (toadPhase == 2 ? 3 : 0) : 2;
			if (phase != toadPhase) {
				toadPhase = phase;
				toadTimer = 0;
			}
			else {
				toadTimer++;
			}
			if (toadPhase == 3 && toadTimer >= 8) {
				toadPhase = 0;
				toadTimer = 0;
			}
		}

		public int ToadFrame => Toadstool.FrameFor(toadPhase, Player.velocity, toadTimer);

		private void Puff() {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item16 with { Pitch = 0.2f, Volume = 0.7f }, Player.Center);
			for (int i = 0; i < 18; i++) {
				if (SafeSpawn.TryNewDust(Player.position, Player.width, Player.height, i % 2 == 0 ? DustID.PinkTorch : DustID.GlowingMushroom, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(3f, 3f);
				}
			}
		}

		/// <summary>The toad hides the player's own look (every layer but its own).</summary>
		public override void HideDrawLayers(PlayerDrawSet drawInfo) {
			if (!Toad) {
				return;
			}
			PlayerDrawLayer own = ModContent.GetInstance<PolymorphDrawLayer>();
			foreach (PlayerDrawLayer layer in PlayerDrawLayerLoader.Layers) {
				if (layer != own) {
					layer.Hide();
				}
			}
		}
	}

	/// <summary>Draws a polymorphed player as the Toadstool, its feet on the player's, facing the player's way.</summary>
	public sealed class PolymorphDrawLayer : PlayerDrawLayer
	{
		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.LastVanillaLayer);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) => drawInfo.drawPlayer.GetModPlayer<PolymorphPlayer>().Toad;

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			Player p = drawInfo.drawPlayer;
			if (drawInfo.shadow != 0f) {
				return;                                              // no afterimages
			}
			Vector2 feet = new(p.position.X + p.width * 0.5f, p.position.Y + p.height);
			Vector2 screen = feet - Main.screenPosition + new Vector2(0f, p.gfxOffY);
			Color light = Lighting.GetColor((int)(p.Center.X / 16f), (int)(p.Center.Y / 16f));
			Toadstool.AddFormDrawData(ref drawInfo, screen, p.GetModPlayer<PolymorphPlayer>().ToadFrame, p.direction == 1, light);
		}
	}

	/// <summary>
	/// "it can be damaged by other players while polymorphed": other players' projectiles and melee swings hurt a polymorphed
	/// player even with PvP off, the way vanilla's PvP does it (decompiled <c>Projectile.Damage</c> and
	/// <c>Player.ItemCheck_MeleeHitPVP</c>: the attacker's client calls <c>Hurt(..., pvp: true)</c> on the victim and sends
	/// <c>NetMessage.SendPlayerHurt</c>; the projectile's per-player immunity, 40 ticks; the victim's own hurt immunity stops a
	/// swing landing twice). Only when someone is polymorphed (<see cref="ToadCount"/>, counted once a tick), only on the
	/// attacker's client.
	/// </summary>
	public sealed class PolymorphPvP : ModSystem
	{
		/// <summary>Polymorphed players this tick (every side).</summary>
		public static int ToadCount { get; private set; }

		public override void PostUpdatePlayers() {
			int n = 0;
			foreach (Player p in Main.ActivePlayers) {
				if (!p.dead && p.GetModPlayer<PolymorphPlayer>().Toad) {
					n++;
				}
			}
			ToadCount = n;
		}

		public override void ClearWorld() {
			ToadCount = 0;
		}

		/// <summary>Can <paramref name="attacker"/>'s hit land on <paramref name="victim"/> now?</summary>
		internal static bool Vulnerable(Player victim, int attacker) =>
			victim.active && !victim.dead && !victim.immune && victim.whoAmI != attacker && victim.GetModPlayer<PolymorphPlayer>().Toad;
	}

	/// <summary>Other players' projectiles on a polymorphed player (the projectile owner's client).</summary>
	public sealed class PolymorphPvPProjectile : GlobalProjectile
	{
		public override void PostAI(Projectile projectile) {
			if (PolymorphPvP.ToadCount == 0 || projectile.owner != Main.myPlayer || !projectile.friendly || projectile.hostile
				|| projectile.damage <= 0 || projectile.npcProj || projectile.trap || Main.myPlayer < 0 || Main.myPlayer >= Main.maxPlayers) {
				return;
			}
			if (projectile.ModProjectile?.CanDamage() == false) {
				return;
			}
			Rectangle mine = projectile.Hitbox;
			for (int i = 0; i < Main.maxPlayers; i++) {
				Player victim = Main.player[i];
				if (!PolymorphPvP.Vulnerable(victim, projectile.owner) || projectile.playerImmune[i] > 0 || !projectile.Colliding(mine, victim.Hitbox)) {
					continue;
				}
				int dir = victim.Center.X >= projectile.Center.X ? 1 : -1;
				int damage = Main.DamageVar(projectile.damage, Main.player[projectile.owner].luck);
				PlayerDeathReason reason = PlayerDeathReason.ByProjectile(projectile.owner, projectile.whoAmI);
				victim.Hurt(reason, damage, dir, out Player.HurtInfo info, pvp: true, quiet: false, -1, projectile.IsDamageDodgable());
				if (Main.netMode != NetmodeID.SinglePlayer) {
					NetMessage.SendPlayerHurt(i, info);
				}
				projectile.playerImmune[i] = 40;
				if (projectile.penetrate > 0 && --projectile.penetrate == 0) {
					projectile.Kill();
					return;
				}
			}
		}
	}

	/// <summary>Other players' melee swings on a polymorphed player (the swinger's client, with vanilla's swing hitbox).</summary>
	public sealed class PolymorphPvPItem : GlobalItem
	{
		public override void MeleeEffects(Item item, Player player, Rectangle hitbox) {
			if (PolymorphPvP.ToadCount == 0 || player.whoAmI != Main.myPlayer || item.damage <= 0 || item.noMelee) {
				return;
			}
			for (int i = 0; i < Main.maxPlayers; i++) {
				Player victim = Main.player[i];
				if (!PolymorphPvP.Vulnerable(victim, player.whoAmI) || !hitbox.Intersects(victim.Hitbox)) {
					continue;
				}
				int dir = victim.Center.X >= player.Center.X ? 1 : -1;
				int damage = Main.DamageVar(player.GetWeaponDamage(item), player.luck);
				PlayerDeathReason reason = PlayerDeathReason.ByPlayerItem(player.whoAmI, item);
				victim.Hurt(reason, damage, dir, out Player.HurtInfo info, pvp: true, quiet: false, -1);
				if (Main.netMode != NetmodeID.SinglePlayer) {
					NetMessage.SendPlayerHurt(i, info);
				}
			}
		}
	}
}
