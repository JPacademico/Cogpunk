using System;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.GameContent.Bestiary;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Templates
{
	/// <summary>
	/// Base for small layered ground enemies (the Mech Army's machines, the Puxa-frango; moved here from MechArmy/MechWalker
	/// on 2026-10-28 so slices share it): a <see cref="StateMachineNPC"/> that runs on the ground like a fighter, retargets
	/// on the server, and draws three planes from grid sheets with a horizontal parallax (<see cref="DepthLayers.DrawWalker"/>;
	/// far <c>Name_Far</c>, middle = the NPC texture, near <c>Name_Near</c>, plus an optional <c>Name_Glow</c> at full
	/// brightness). Cell sizes come from a generated <c>*RigData.cs</c>, so art and code agree.
	/// <para>D2: movement runs on every side from synced state (vanilla collision, like a fighter); the server picks the
	/// target and every decision. D1: no allocation; textures cached once per type on clients.</para>
	/// </summary>
	public abstract class GridWalkerNPC : StateMachineNPC
	{
		/// <summary>Largest parallax shift of the far and near planes at the edge of the screen, px.</summary>
		public const float MaxParallax = 2f;
		public const int RetargetInterval = 20;

		protected abstract int CellWidth { get; }
		protected abstract int CellHeight { get; }
		protected abstract int OriginX { get; }
		protected abstract int OriginY { get; }
		protected abstract int FrameCount { get; }

		/// <summary>Px between the sheet's cells (the generators leave 1 art px = 2 game px).</summary>
		protected virtual int CellPadding => 2;

		/// <summary>The far, near and glow sheets of this type (static per type, loaded on clients).</summary>
		protected abstract Asset<Texture2D> FarSheet { get; }
		protected abstract Asset<Texture2D> NearSheet { get; }
		protected abstract Asset<Texture2D> GlowSheet { get; }

		/// <summary>The frame to draw (visual only, set in <c>FindFrame</c>).</summary>
		protected int Frame;

		/// <summary>The glow sheet's brightness this frame (0 hides it).</summary>
		protected virtual float GlowStrength => 1f;

		/// <summary>Where the cells' origin is drawn, in world space: the hitbox's bottom centre for a walker (its feet).
		/// A swimmer with no feet (the Cogtuna, 2026-11-04) puts its origin under its centre instead.</summary>
		protected virtual Vector2 DrawAnchor => NPC.Bottom;

		protected bool Grounded => NPC.velocity.Y == 0f;

		protected Player Target => NPC.HasValidTarget ? Main.player[NPC.target] : null;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = FrameCount;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Velocity = 1f });
			LoadSheets();
		}

		/// <summary>Request the far/near/glow sheets into the subclass's static fields (clients only).</summary>
		protected abstract void LoadSheets();

		/// <summary>The bestiary's biome tag (surface by default).</summary>
		protected virtual IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Surface;

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryBiome,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		/// <summary>Server: the closest player, every <see cref="RetargetInterval"/> ticks or when the target is lost.</summary>
		protected void Retarget() {
			if (IsAuthority && (Timer % RetargetInterval == 1f || !NPC.HasValidTarget)) {
				int old = NPC.target;
				NPC.TargetClosest(false);
				if (NPC.target != old) {
					NPC.netUpdate = true;
				}
			}
		}

		/// <summary>Accelerates towards <paramref name="dir"/> x <paramref name="speed"/> (0 = brake), steps up single tiles,
		/// and jumps when a wall stops it on the ground. Same inputs on every side.</summary>
		protected void Run(int dir, float speed, float accel, float jumpSpeed) {
			float want = dir * speed;
			if (NPC.velocity.X < want) {
				NPC.velocity.X = Math.Min(want, NPC.velocity.X + accel);
			}
			else if (NPC.velocity.X > want) {
				NPC.velocity.X = Math.Max(want, NPC.velocity.X - accel);
			}
			Collision.StepUp(ref NPC.position, ref NPC.velocity, NPC.width, NPC.height, ref NPC.stepSpeed, ref NPC.gfxOffY);
			if (dir != 0 && NPC.collideX && Grounded) {
				NPC.velocity.Y = -jumpSpeed;
			}
		}

		/// <summary>Faces the way it moves (or <paramref name="fallback"/> when nearly still).</summary>
		protected void FaceMotion(int fallback) {
			int dir = Math.Abs(NPC.velocity.X) > 0.15f ? Math.Sign(NPC.velocity.X) : fallback;
			if (dir != 0) {
				NPC.direction = NPC.spriteDirection = dir;
			}
		}

		public override void FindFrame(int frameHeight) {
			Frame = Math.Clamp(PickFrame(), 0, FrameCount - 1);
			NPC.frame.Y = Frame * frameHeight;
		}

		/// <summary>The frame for the current state (visual only, client side).</summary>
		protected abstract int PickFrame();

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			bool dummy = NPC.IsABestiaryIconDummy;
			float scale = dummy ? NPC.scale : 1f;
			Vector2 anchor = DrawAnchor - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;              // the art faces left
			Color light = NPC.GetAlpha(drawColor);
			int frame = dummy ? 0 : Frame;
			Texture2D middle = TextureAssets.Npc[Type].Value;
			DepthLayers.DrawWalker(spriteBatch, FarSheet?.Value, middle, NearSheet?.Value, frame, CellWidth, CellHeight,
				CellPadding, OriginX, OriginY, anchor, light, flip, dummy ? 0f : MaxParallax, scale);
			float glow = GlowStrength;
			if (glow > 0f && GlowSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, GlowSheet.Value, frame, 1, CellWidth, CellHeight, CellPadding, OriginX, OriginY,
					anchor, 0, Color.White * glow * NPC.Opacity, flip, scale);
			}
			DrawExtras(spriteBatch, anchor, light, flip, scale, dummy);
			return false;
		}

		/// <summary>Anything drawn on top of the planes (the Annoy-o-tron's beacon).</summary>
		protected virtual void DrawExtras(SpriteBatch spriteBatch, Vector2 anchor, Color light, bool flip, float scale, bool dummy) {
		}
	}
}
