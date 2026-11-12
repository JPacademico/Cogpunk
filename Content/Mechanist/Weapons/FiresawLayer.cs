using System;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// Draws the <see cref="Firesaw"/> in its wielder's hand (2026-11-10; the item is <c>noUseGraphic</c>): the saw at the
	/// swing's angle with its chain running (<c>FiresawSwing.png</c>, <see cref="Firesaw.Frames"/> frames, one every
	/// <see cref="Firesaw.FrameTicks"/> ticks), its fire on top while it burns (<c>FiresawFire.png</c>, at full brightness),
	/// and through the slash a smear (D4 rule 10): the saw again where it was the last <see cref="Ghosts"/> ticks, fainter
	/// each tick back, under the real one (the Metal Wrench's smear, <c>MetalWrenchSmearLayer</c>).
	/// <para>Under it all, the phantom slash (2026-11-10b, user: "add a slight phantom slash trail to each swing so it has more
	/// cool motion animation"): a crescent over the arc the blade swept in the last <see cref="TrailTicks"/> ticks, round the
	/// shoulder (vanilla's arm points along the blade, so the blade's line runs through the shoulder: the hand
	/// <see cref="ArmReach"/> px out, decompiled <c>Player.GetFrontHandPosition</c>), its leading edge on the blade. The sheets
	/// (<c>FiresawTrail.png</c>, <c>FiresawTrailFire.png</c> out to the fire's reach) hold <see cref="TrailFrames"/> crescents,
	/// each <see cref="TrailStep"/> longer; the one nearest the sweep is turned onto the blade and mirrored for an up-slash,
	/// added onto what is behind it (alpha 0 under premultiplied blending: light, never a dark smear) at
	/// <see cref="TrailOpacity"/>, fuller the faster the blade moves. It grows through the slash and shrinks into the blade as
	/// the swing settles.</para>
	/// <para>Each copy is posed exactly as vanilla poses a held swing (decompiled <c>PlayerDrawLayers.DrawPlayer_27_HeldItem</c>:
	/// at <c>itemLocation</c>, turned by <c>itemRotation</c>, the item's scale, mirrored by <c>itemEffect</c>), except that its
	/// pivot is the grip on the blade's axis (<see cref="Firesaw.GripX"/>, <see cref="Firesaw.GripY"/>) instead of the
	/// sprite's corner, so the hand holds the grip with the fuel canister behind it. Every client draws every player's from
	/// the synced use (<see cref="Firesaw.SwingAngle(Player, int)"/>) and the synced flame. D1: at most 9 draws, textures
	/// cached on clients, no allocation. D0: textures never touched on a dedicated server; a missing one draws nothing; a
	/// non-finite sweep draws no trail.</para>
	/// </summary>
	public sealed class FiresawLayer : PlayerDrawLayer
	{
		public const int Ghosts = 3;
		private static readonly float[] Opacity = { 0.45f, 0.28f, 0.13f };

		// --- the phantom slash (art/mechanist/make_firesaw_art.py: crescent frames, their pivot on the shoulder) ---
		public const int TrailFrames = 6;
		public const float TrailStep = 24f * MathHelper.Pi / 180f;   // frame k spans (k + 1) steps
		public const int TrailTicks = 3;                             // the sweep it shows: the last 3 ticks
		public const float TrailMin = 0.2f;                          // radians: a shorter sweep shows none
		public const float TrailFull = 1.4f;                         // radians: a sweep this long shows at full opacity
		public const float TrailOpacity = 0.5f;                      // "slight"
		public const float ArmReach = 10f;                           // the hand's distance out along the blade from the shoulder
		private const int TrailW = 168, TrailH = 96, TrailPivotX = 76, TrailPivotY = 92;
		private const int FireTrailW = 226, FireTrailH = 128, FireTrailPivotX = 102, FireTrailPivotY = 124;

		private static Asset<Texture2D> saw, fire, trail, fireTrail;
		private static int sawType = -1;

		public override void Load() {
			saw = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/FiresawSwing");
			fire = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/FiresawFire");
			trail = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/FiresawTrail");
			fireTrail = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/FiresawTrailFire");
		}

		public override void Unload() {
			saw = fire = trail = fireTrail = null;
			sawType = -1;
		}

		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.HeldItem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			if (sawType < 0) {
				sawType = ModContent.ItemType<Firesaw>();
			}
			Player player = drawInfo.drawPlayer;
			return drawInfo.shadow == 0f && player.itemAnimation > 0 && player.HeldItem.type == sawType && !player.dead && !player.frozen
				&& !player.pulley;
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (saw?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			bool burning = Firesaw.Burning(player) && fire?.IsLoaded == true;
			float scale = player.GetAdjustedItemScale(player.HeldItem);
			Color light = player.HeldItem.GetAlpha(Lighting.GetColor((int)(player.Center.X / 16f), (int)(player.Center.Y / 16f)));
			int frame = (int)(Main.GameUpdateCount / Firesaw.FrameTicks % Firesaw.Frames);
			float done = Firesaw.Done(player);
			if (done >= Firesaw.WindEnd && done < Firesaw.OverEnd) {   // the smear: through the slash and its overshoot
				AddTrail(ref drawInfo, player, burning, scale);
				for (int k = Ghosts; k >= 1; k--) {
					if (Firesaw.Done(player, k) < Firesaw.WindEnd - 0.05f) {
						continue;                                  // nothing to trail before the slash starts
					}
					float ghost = Firesaw.SwingAngle(player, k);
					Add(ref drawInfo, player, saw.Value, Firesaw.Size, Firesaw.GripY, frame, ghost, light * Opacity[k - 1], scale);
					if (burning) {
						Add(ref drawInfo, player, fire.Value, Firesaw.FireSize, Firesaw.FireGripY, frame, ghost, Color.White * Opacity[k - 1], scale);
					}
				}
			}
			float facing = Firesaw.SwingAngle(player);
			Add(ref drawInfo, player, saw.Value, Firesaw.Size, Firesaw.GripY, frame, facing, light, scale);
			if (burning) {
				Add(ref drawInfo, player, fire.Value, Firesaw.FireSize, Firesaw.FireGripY, frame, facing, Color.White, scale);
			}
		}

		/// <summary>The phantom slash: the crescent nearest the blade's sweep over the last <see cref="TrailTicks"/> ticks, its
		/// pivot on the shoulder, its leading edge along the blade, mirrored when the blade turns counter-clockwise on screen.</summary>
		private static void AddTrail(ref PlayerDrawSet drawInfo, Player player, bool burning, float scale) {
			Asset<Texture2D> sheet = burning ? fireTrail : trail;
			if (sheet?.IsLoaded != true) {
				return;
			}
			float facing = Firesaw.SwingAngle(player);
			Vector2 now = SwingPose.BladeDirection(player, facing);
			Vector2 back = SwingPose.BladeDirection(player, Firesaw.SwingAngle(player, TrailTicks));
			float sweep = MathF.Atan2(back.X * now.Y - back.Y * now.X, Vector2.Dot(back, now));   // + clockwise on screen
			float span = MathF.Abs(sweep);
			if (!float.IsFinite(span) || span < TrailMin) {
				return;
			}
			int w = burning ? FireTrailW : TrailW, h = burning ? FireTrailH : TrailH;
			int frame = Math.Clamp((int)(span / TrailStep + 0.5f), 1, TrailFrames) - 1;
			Rectangle source = new(0, frame * (h + Firesaw.Gap), w, h);
			if (source.Bottom > sheet.Value.Height) {
				return;
			}
			SwingPose.Compute(player, facing, out Vector2 hand, out _);
			Vector2 location = drawInfo.Position + (hand - now * ArmReach - player.position);
			Vector2 at = new((int)(location.X - Main.screenPosition.X), (int)(location.Y - Main.screenPosition.Y));
			bool clockwise = sweep > 0f;
			int pivotX = burning ? FireTrailPivotX : TrailPivotX, pivotY = burning ? FireTrailPivotY : TrailPivotY;
			Vector2 origin = new(pivotX, clockwise ? pivotY : h - pivotY);
			float reach = burning ? Firesaw.FireReach : Firesaw.Reach;
			float size = (ArmReach + reach * scale) / (ArmReach + reach);
			float opacity = TrailOpacity * MathHelper.Clamp(span / TrailFull, 0.35f, 1f);
			Color color = new Color(255, 255, 255, 0) * opacity;      // alpha 0: added onto what is behind it
			drawInfo.DrawDataCache.Add(new DrawData(sheet.Value, at, source, color, MathF.Atan2(now.Y, now.X), origin, size,
				clockwise ? SpriteEffects.None : SpriteEffects.FlipVertically));
		}

		/// <summary>One copy of a sheet (square frames of <paramref name="size"/>, <see cref="Firesaw.Gap"/> px apart) posed at
		/// <paramref name="facing"/>, pivoting on the grip.</summary>
		private static void Add(ref PlayerDrawSet drawInfo, Player player, Texture2D sheet, int size, int gripY, int frame, float facing,
			Color color, float scale) {
			Rectangle source = new(0, frame * (size + Firesaw.Gap), size, size);
			if (source.Bottom > sheet.Height) {
				return;
			}
			SwingPose.Compute(player, facing, out Vector2 hand, out float rotation);
			Vector2 location = drawInfo.Position + (hand - player.position);   // as PlayerDrawSet.ItemLocation is made
			Vector2 at = new((int)(location.X - Main.screenPosition.X), (int)(location.Y - Main.screenPosition.Y));
			Vector2 origin = new(player.direction == 1 ? Firesaw.GripX : size - Firesaw.GripX, player.gravDir == -1f ? size - gripY : gripY);
			drawInfo.DrawDataCache.Add(new DrawData(sheet, at, source, color, rotation, origin, scale, drawInfo.itemEffect));
		}
	}
}
