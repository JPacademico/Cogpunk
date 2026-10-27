using System;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Map
{
	/// <summary>
	/// The Mysterious Map's guidance arrow: a brass compass needle with a cog hub and an aether tip that circles a player
	/// holding the map at <see cref="Radius"/> px and points at <see cref="MapTargetSystem.Target"/>. Every player holding
	/// one shows it (the held item is synced); it is a draw layer, so nothing runs on a dedicated server (D1, D2).
	/// <para>D4: the arrow is never rotated at runtime. The sheet holds <see cref="Directions"/> pre-rendered headings
	/// (one every 22.5 degrees, heading 0 = right, clockwise in screen space), and the closest one is drawn at whole pixels
	/// on the circle. The aether glow (its own texture) pulses faster as the player gets close.</para>
	/// </summary>
	public sealed class MysteriousMapArrowLayer : PlayerDrawLayer
	{
		public const int Directions = 16;
		public const float Radius = 46f;
		public const int FrameSize = 40, FrameStride = 42;
		private const float NearDistance = 60f * 16f;    // the pulse quickens inside this

		private static Asset<Texture2D> arrow;
		private static Asset<Texture2D> glow;
		private static int mapType = -1;

		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			const string path = "Cogpunk/Content/Junkyard/Map/MysteriousMapArrow";
			arrow = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
			glow = ModContent.HasAsset(path + "_Glow") ? ModContent.Request<Texture2D>(path + "_Glow") : null;
		}

		public override void Unload() {
			arrow = null;
			glow = null;
			mapType = -1;
		}

		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.FrontAccFront);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			if (mapType < 0) {
				mapType = ModContent.ItemType<MysteriousMap>();
			}
			Player player = drawInfo.drawPlayer;
			return drawInfo.shadow == 0f && !player.dead && !player.ghost && player.HeldItem.type == mapType;
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (arrow?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			Vector2 centre = player.MountedCenter;
			Vector2 toTarget = MapTargetSystem.TargetWorld - centre;
			float distance = toTarget.Length();
			float angle = distance > 1f ? MathF.Atan2(toTarget.Y, toTarget.X) : MathHelper.PiOver2;
			int heading = ((int)MathF.Round(angle / MathHelper.TwoPi * Directions) % Directions + Directions) % Directions;
			float snapped = heading * MathHelper.TwoPi / Directions;
			Vector2 world = centre + new Vector2(MathF.Cos(snapped), MathF.Sin(snapped)) * Radius;
			Vector2 at = world - Main.screenPosition;
			Vector2 position = new(MathF.Round(at.X - FrameSize * 0.5f), MathF.Round(at.Y - FrameSize * 0.5f + player.gfxOffY));
			Rectangle source = new(0, heading * FrameStride, FrameSize, FrameSize);
			Color light = Lighting.GetColor(world.ToTileCoordinates());
			drawInfo.DrawDataCache.Add(new DrawData(arrow.Value, position, source, Color.Lerp(light, Color.White, 0.45f)));
			if (glow?.IsLoaded == true) {
				float speed = distance < NearDistance ? 9f : 3f;
				float pulse = 0.6f + 0.4f * MathF.Sin(Main.GlobalTimeWrappedHourly * speed);
				drawInfo.DrawDataCache.Add(new DrawData(glow.Value, position, source, Color.White * pulse));
			}
		}
	}
}
