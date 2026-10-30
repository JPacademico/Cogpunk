using System;
using Cogpunk.Content.Junkyard.NPCs;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.TarTyrant.TarTyrantRigData;

namespace Cogpunk.Content.Bosses.TarTyrant.NPCs
{
	/// <summary>
	/// A condensed tar bubble burped up by Tar Tyrant (user, 2026-10-29): it drifts slowly after its target, swelling over
	/// <see cref="GrowTicks"/> (3 s); popped before then it is simply gone, otherwise it bursts into
	/// <see cref="SlimesPerBurst"/> Living Tar. An NPC, so players can pop it (like vanilla's Detonating Bubble in Duke
	/// Fishron's fight), with <see cref="Life"/> life; touching it does <see cref="ContactDamage"/> and gives the Tar Plague.
	/// <para>D2: the server decides the burst and spawns the slimes; the drift is the same math on every side from the
	/// synced position, velocity, target and age (<c>ai[0]</c>), resynced every <see cref="ResyncInterval"/> ticks. Seven
	/// sizes drawn by the generator (never scaled at runtime), two wobble frames each; the hitbox grows with the drawing.
	/// D0: it never spawns bubbles itself, and its slimes don't either.</para>
	/// </summary>
	public class TarTyrantBubble : CogpunkNPC
	{
		public const int Life = 40, ContactDamage = 30;      // Expert: one or two hits of a T3 weapon pop it
		public const int GrowTicks = 180;
		public const int SlimesPerBurst = 2;
		public const float DriftSpeed = 0.9f, DriftAccel = 0.035f, LaunchDrag = 0.96f;
		public const float OrbitRadius = 5f * 16f;          // each bubble drifts towards its own spot around the target
		public const float OrbitTurn = 0.01f;
		public const int ResyncInterval = 30;
		public const int WobbleTicks = 10;

		private ref float Age => ref NPC.ai[0];
		private int sizeShown = -1;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = R.BubbleSizes * 2;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Hide = true });
			NPCID.Sets.SpecificDebuffImmunity[Type][ModContent.BuffType<TarPlague>()] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		public override void SetDefaults() {
			NPC.width = NPC.height = Diameter(0);
			SetExpertStats(Life, ContactDamage, 0);
			NPC.knockBackResist = 0.4f;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.aiStyle = -1;
			NPC.value = 0f;
			NPC.npcSlots = 0f;
			NPC.HitSound = SoundID.NPCHit1 with { Pitch = 0.3f };
			NPC.DeathSound = SoundID.Item54 with { Pitch = -0.3f };
		}

		/// <summary>The hitbox for size step <paramref name="step"/>: most of the drawn bubble.</summary>
		public static int Diameter(int step) => (int)(R.BubbleRadius[Math.Clamp(step, 0, R.BubbleSizes - 1)] * 2 * 0.85f);

		public int Step => Math.Clamp((int)(Age * R.BubbleSizes / GrowTicks), 0, R.BubbleSizes - 1);

		public override bool CheckActive() => false;          // it lives 3 s; never despawned by distance

		public override void AI() {
			Age++;
			int step = Step;
			if (step != sizeShown) {
				sizeShown = step;
				Vector2 centre = NPC.Center;
				NPC.width = NPC.height = Diameter(step);
				NPC.Center = centre;
			}
			Player target = NPC.target >= 0 && NPC.target < Main.maxPlayers && Main.player[NPC.target].active && !Main.player[NPC.target].dead
				? Main.player[NPC.target] : null;
			Vector2 want = Vector2.Zero;
			if (target != null) {
				float angle = NPC.whoAmI * 2.4f + Age * OrbitTurn;             // the same on every side (whoAmI is synced)
				Vector2 spot = target.Center + new Vector2(MathF.Cos(angle), MathF.Sin(angle) * 0.6f - 0.4f) * OrbitRadius;
				want = (spot - NPC.Center).SafeNormalize(Vector2.Zero) * DriftSpeed;
			}
			want.Y += MathF.Sin(Age * 0.07f + NPC.whoAmI) * 0.4f;       // it bobs as it floats
			NPC.velocity *= LaunchDrag;
			NPC.velocity += (want - NPC.velocity) * DriftAccel;
			MathSafety.Sanitize(ref NPC.velocity);
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				if ((int)Age % ResyncInterval == 0) {
					NPC.netUpdate = true;
				}
				if (Age >= GrowTicks) {
					Burst();
					return;
				}
			}
			if (!Main.dedServ) {
				Lighting.AddLight(NPC.Center, 0.12f, 0.07f, 0.04f);
				if (Age >= GrowTicks - 30 && (int)Age % 6 == 0 && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, ModContent.DustType<TarSplash>(), out Dust d)) {
					d.velocity *= 0.3f;                         // about to go: it sweats tar
				}
			}
		}

		/// <summary>Server: it bursts. Two Living Tar fall out of it (no loot from them: they are the boss's tar), then it is
		/// gone (an instant-kill strike, which the clients see as the splash in <see cref="HitEffect"/>).</summary>
		private void Burst() {
			int type = ModContent.NPCType<LivingTar>();
			for (int i = 0; i < SlimesPerBurst; i++) {
				if (!SafeSpawn.TryNewNPC(NPC.GetSource_FromAI(), (int)NPC.Center.X, (int)NPC.Center.Y + 9, type, out NPC slime)) {
					break;
				}
				if (slime.ModNPC is LivingTar tar) {
					tar.FromBoss = true;
				}
				slime.velocity = new Vector2(i == 0 ? -2f : 2f, -2.5f);
				slime.target = NPC.target;
				slime.netUpdate = true;
			}
			NPC.StrikeInstantKill();
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			target.AddBuff(ModContent.BuffType<TarPlague>(), TarTyrant.PlagueTicks);
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 16;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, ModContent.DustType<TarSplash>(), out Dust d, hit.HitDirection * 1.5f, -2f)) {
					d.velocity *= NPC.life > 0 ? 1f : 2.2f;
				}
			}
			if (NPC.life <= 0) {
				SoundEngine.PlaySound(SoundID.NPCDeath13 with { Pitch = 0.1f, Volume = 0.6f, MaxInstances = 4 }, NPC.Center);
			}
		}

		public override void FindFrame(int frameHeight) {
			int wobble = (int)(Age / WobbleTicks) % 2;
			NPC.frame = new Rectangle(0, (Step * 2 + wobble) * (R.BubbleCell + 2), R.BubbleCell, R.BubbleCell);
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			Texture2D texture = TextureAssets.Npc[Type].Value;
			if (NPC.frame.Bottom > texture.Height) {
				return false;
			}
			Vector2 centre = NPC.Center - screenPos + new Vector2(0f, NPC.gfxOffY);
			Vector2 position = new(MathF.Round(centre.X - R.BubbleCell * 0.5f), MathF.Round(centre.Y - R.BubbleCell * 0.5f));
			spriteBatch.Draw(texture, position, NPC.frame, NPC.GetAlpha(drawColor), 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
			return false;
		}
	}
}
