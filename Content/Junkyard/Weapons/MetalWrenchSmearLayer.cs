using Cogpunk.Core.Combat;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The Metal Wrench slam's smear (2026-11-05b; D4 rule 10: smears for swings): while the wrench comes down
	/// (<see cref="MetalWrench.HangEnd"/> to <see cref="MetalWrench.ImpactAt"/>, and a tick past the strike) the wrench is drawn
	/// again where it was <see cref="Ghosts"/> ticks ago, fainter each tick back, under the real one.
	/// <para>Each ghost is the item sprite posed exactly as vanilla poses the held swing (decompiled
	/// <c>PlayerDrawLayers.DrawPlayer_27_HeldItem</c>: at <c>itemLocation</c>, origin at the handle corner, the item's scale and
	/// flip) at the slam's angle for that tick (<see cref="MetalWrench.SlamAngle(Player, int)"/>), so it needs no stored
	/// state: every client draws every player's from the synced use. D1: at most <see cref="Ghosts"/> draws, no allocation.
	/// D4: the sprite is the item's own; the fade is opacity only.</para>
	/// </summary>
	public sealed class MetalWrenchSmearLayer : PlayerDrawLayer
	{
		public const int Ghosts = 3;
		private static readonly float[] Opacity = { 0.42f, 0.26f, 0.12f };
		private static int wrenchType = -1;

		public override void Unload() {
			wrenchType = -1;
		}

		public override Position GetDefaultPosition() => new BeforeParent(PlayerDrawLayers.HeldItem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			if (wrenchType < 0) {
				wrenchType = ModContent.ItemType<MetalWrench>();
			}
			Player player = drawInfo.drawPlayer;
			if (drawInfo.shadow != 0f || player.itemAnimation <= 0 || player.HeldItem.type != wrenchType || player.dead || player.frozen) {
				return false;
			}
			float done = MetalWrench.Done(player);
			return done >= MetalWrench.HangEnd && done < MetalWrench.ImpactAt + 1f / System.Math.Max(1, player.itemAnimationMax);
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			Player player = drawInfo.drawPlayer;
			if (player.HeldItem.ModItem is not MetalWrench wrench) {
				return;
			}
			Main.instance.LoadItem(wrenchType);
			Texture2D texture = TextureAssets.Item[wrenchType].Value;
			Vector2 origin = new(texture.Width * 0.5f - texture.Width * 0.5f * player.direction, player.gravDir == -1f ? 0f : texture.Height);
			float scale = player.GetAdjustedItemScale(player.HeldItem);
			Color light = Lighting.GetColor((int)((drawInfo.Position.X + player.width * 0.5f) / 16f), (int)((drawInfo.Position.Y + player.height * 0.5f) / 16f));
			for (int k = 0; k < Ghosts; k++) {
				float done = MetalWrench.Done(player, k + 1);
				if (done < MetalWrench.HangEnd) {
					break;                                     // nothing to trail before it starts down
				}
				SwingPose.Compute(player, wrench.SlamAngle(player, k + 1), out Vector2 hand, out float rotation);
				Vector2 location = drawInfo.Position + (hand - player.position);   // as PlayerDrawSet.ItemLocation is made
				Vector2 at = new((int)(location.X - Main.screenPosition.X), (int)(location.Y - Main.screenPosition.Y));
				drawInfo.DrawDataCache.Add(new DrawData(texture, at, null, player.HeldItem.GetAlpha(light) * Opacity[k], rotation, origin, scale,
					drawInfo.itemEffect));
			}
		}
	}
}
