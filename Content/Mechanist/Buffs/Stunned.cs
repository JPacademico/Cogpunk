using System;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Buffs
{
	/// <summary>
	/// Stunned (the Barrel Gun's fish, user-set 2026-11-11b: "a chance to stun enemies (only stun basic enemies, not bosses or
	/// mini bosses)"): the enemy stops acting while it lasts (<see cref="StunnedNPC"/>). Only <see cref="StunnedNPC.CanStun"/>
	/// enemies take it.
	/// </summary>
	public class Stunned : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
		}
	}

	/// <summary>
	/// What <see cref="Stunned"/> does, on every side: its AI is skipped (vanilla's gravity, applied after the AI, still pulls
	/// a walker down; a flyer hangs where it was), it slides to a stop, its animation holds, it can't touch anyone, and gold
	/// stars circle its head. The jade curse's petrification works the same way (<c>JadeCurseNPC</c>).
	/// <para>Who can be stunned (<see cref="CanStun"/>): basic enemies only. Not bosses or mini-bosses
	/// (<see cref="CogpunkSets.IsBossOrMiniboss"/>), nor a part of a body (worms, linked parts: a frozen head would drag its
	/// tail), nor critters, town NPCs, projectile NPCs or anything that can't be hurt.</para>
	/// <para>D2: the buff is the sync: the hitting player's client adds it, vanilla sends it to the server and the server to
	/// every client (decompiled <c>NPC.AddBuff</c>: message 53, then 54), so every side skips the same ticks. D1: one buff
	/// check a tick per NPC; the stars on clients only, from a cached texture.</para>
	/// </summary>
	public sealed class StunnedNPC : GlobalNPC
	{
		public const int StarFrames = 2, StarSize = 10, StarStride = 12, StarCount = 3;
		public const float StarOrbit = 12f, StarSpin = 0.12f;

		private static Asset<Texture2D> stars;
		private bool wasStunned;
		private Rectangle heldFrame;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => lateInstantiation && !entity.townNPC && !entity.friendly;

		public override void SetStaticDefaults() {
			if (!Main.dedServ) {
				stars = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Buffs/StunStars");
			}
		}

		public override void Unload() {
			stars = null;
		}

		/// <summary>A basic enemy that a stun may hold (bounds-checked through <see cref="CogpunkSets"/>).</summary>
		public static bool CanStun(NPC npc) {
			if (npc == null || !npc.active || npc.friendly || npc.townNPC || npc.dontTakeDamage || npc.immortal || npc.lifeMax <= 5) {
				return false;
			}
			int type = npc.type;
			if (type <= NPCID.None || type >= NPCLoader.NPCCount || NPCID.Sets.CountsAsCritter[type] || NPCID.Sets.ProjectileNPC[type]) {
				return false;
			}
			if (npc.realLife >= 0 || npc.aiStyle == NPCAIStyleID.Worm || CogpunkSets.IsBossOrMiniboss(npc)) {
				return false;
			}
			int stun = ModContent.BuffType<Stunned>();
			return stun < npc.buffImmune.Length && !npc.buffImmune[stun];
		}

		/// <summary>The hitting player's client: stuns <paramref name="npc"/> for <paramref name="ticks"/> if it can be (vanilla
		/// syncs the buff).</summary>
		public static bool TryStun(NPC npc, int ticks) {
			if (ticks <= 0 || !CanStun(npc)) {
				return false;
			}
			npc.AddBuff(ModContent.BuffType<Stunned>(), ticks);
			return true;
		}

		public static bool IsStunned(NPC npc) => npc.HasBuff(ModContent.BuffType<Stunned>());

		public override bool PreAI(NPC npc) {
			if (!IsStunned(npc)) {
				return true;
			}
			npc.velocity.X *= 0.8f;
			if (npc.noGravity) {
				npc.velocity.Y *= 0.8f;
			}
			return false;
		}

		public override void PostAI(NPC npc) {
			bool stunned = IsStunned(npc);
			if (stunned != wasStunned) {
				wasStunned = stunned;
				if (stunned) {
					heldFrame = npc.frame;
				}
			}
		}

		/// <summary>Held in the frame it was stunned in (vanilla's animation runs before this).</summary>
		public override void FindFrame(NPC npc, int frameHeight) {
			if (wasStunned && heldFrame.Height > 0) {
				npc.frame = heldFrame;
			}
		}

		public override bool CanHitPlayer(NPC npc, Player target, ref int cooldownSlot) => !IsStunned(npc);

		public override bool CanHitNPC(NPC npc, NPC target) => !IsStunned(npc);

		/// <summary>Clients: <see cref="StarCount"/> gold stars circling over its head, twinkling.</summary>
		public override void PostDraw(NPC npc, SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			if (!wasStunned || stars?.IsLoaded != true) {
				return;
			}
			Texture2D tex = stars.Value;
			float spin = Main.GlobalTimeWrappedHourly * 60f * StarSpin;
			Vector2 head = new(npc.Center.X, npc.Top.Y - 6f);
			for (int k = 0; k < StarCount; k++) {
				float a = spin + k * MathHelper.TwoPi / StarCount;
				int frame = (int)(Main.GameUpdateCount / 8 + k) % StarFrames;
				Rectangle source = new(0, frame * StarStride, StarSize, StarSize);
				if (source.Bottom > tex.Height) {
					return;
				}
				Vector2 at = head + new Vector2(MathF.Cos(a) * StarOrbit, MathF.Sin(a) * StarOrbit * 0.35f) - screenPos;
				at = new Vector2((int)at.X, (int)at.Y);
				spriteBatch.Draw(tex, at, source, Color.White, 0f, new Vector2(StarSize / 2f), 1f, SpriteEffects.None, 0f);
			}
		}
	}
}
