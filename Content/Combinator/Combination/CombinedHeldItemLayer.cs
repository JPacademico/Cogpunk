using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>Marks where vanilla's held-item drawing starts in the draw list (<see cref="CombinedHeldItemLayer"/>).</summary>
	public sealed class CombinedHeldItemMark : PlayerDrawLayer
	{
		internal static int Start = -1;

		public override Position GetDefaultPosition() => new BeforeParent(PlayerDrawLayers.HeldItem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) => CombinedHeldItemLayer.Shows(drawInfo);

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			Start = drawInfo.DrawDataCache.Count;
		}
	}

	/// <summary>
	/// A combination in the hand looks combined too. Vanilla draws the held item from the item type's own texture
	/// (decompiled <c>PlayerDrawLayers.DrawPlayer_27_HeldItem</c>: <c>TextureAssets.Item[type]</c>, its frame, an origin at the
	/// grip worked out from that frame's size, the swing's rotation and flips). Rather than redo all of that, this layer runs
	/// right after it and swaps the texture in the entries it added for <see cref="CombinedSprites"/>' glued one, moving the
	/// origin by where the item's own sprite sits inside the glued one, mirrored for a flip (the origin is a point on the
	/// drawn quad, and a flip mirrors the texture across it: FNA's <c>SpriteBatch.PushSprite</c>), so the grip stays in the
	/// hand and the rest grows round it. The item's glow mask, drawn from the plain sprite's layout, is hidden.
	/// <para>Only the item sprite: weapons drawn by their own projectile or layer (spears, yoyos, the Firesaw, held guns with
	/// <c>noUseGraphic</c>) show that projectile or layer as before. D1: a loop over the few entries the held item added, no
	/// allocation; clients only (drawing).</para>
	/// </summary>
	public sealed class CombinedHeldItemLayer : PlayerDrawLayer
	{
		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.HeldItem);

		internal static bool Shows(PlayerDrawSet drawInfo) {
			Item held = drawInfo.heldItem;
			return held != null && !held.IsAir && CombinedWeapon.TryGet(held, out CombinedWeapon data) && (data.IsProduct || data.IsStandIn);
		}

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) => Shows(drawInfo);

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			int start = CombinedHeldItemMark.Start;
			CombinedHeldItemMark.Start = -1;
			Item held = drawInfo.heldItem;
			if (start < 0 || start > drawInfo.DrawDataCache.Count || !CombinedWeapon.TryGet(held, out CombinedWeapon data)
				|| !data.TrySprite(held, out CombinedSprite sprite, out Point own)) {
				return;
			}
			Texture2D plain = TextureAssets.Item[held.type].Value;
			Texture2D glow = held.glowMask > 0 && held.glowMask < TextureAssets.GlowMask.Length ? TextureAssets.GlowMask[held.glowMask].Value : null;
			for (int i = start; i < drawInfo.DrawDataCache.Count; i++) {
				DrawData d = drawInfo.DrawDataCache[i];
				if (glow != null && d.texture == glow) {
					d.color = Color.Transparent;
					drawInfo.DrawDataCache[i] = d;
					continue;
				}
				if (d.texture != plain) {
					continue;
				}
				Rectangle src = d.sourceRect ?? plain.Bounds;
				bool fx = (d.effect & SpriteEffects.FlipHorizontally) != 0, fy = (d.effect & SpriteEffects.FlipVertically) != 0;
				float ox = fx ? d.origin.X + (sprite.Width - src.Width - own.X) : d.origin.X + own.X;
				float oy = fy ? d.origin.Y + (sprite.Height - src.Height - own.Y) : d.origin.Y + own.Y;
				d.texture = sprite.Texture;
				d.sourceRect = new Rectangle(0, 0, sprite.Width, sprite.Height);
				d.origin = new Vector2(ox, oy);
				drawInfo.DrawDataCache[i] = d;
			}
		}
	}
}
