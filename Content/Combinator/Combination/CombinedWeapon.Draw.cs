using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;

namespace Cogpunk.Content.Combinator.Combination
{
	// The look of a combination: CombinedSprites' glued texture in the inventory, on the ground and (CombinedHeldItemLayer)
	// in the hand; and a swung blade's hitbox fitted to it.
	public sealed partial class CombinedWeapon
	{
		/// <summary>The pair whose sprite this item shows (a product: its type and its base's; a stand-in: the augment's and its
		/// own type), and where this item's own type sits in that sprite.</summary>
		public bool TrySprite(Item item, out CombinedSprite sprite, out Point ownOffset) {
			sprite = null;
			ownOffset = Point.Zero;
			if (IsProduct) {
				if (CombinedSprites.TryGet(item.type, Base.type, out sprite)) {
					ownOffset = sprite.AugmentOffset;
					return true;
				}
				return false;
			}
			if (IsStandIn && CombinedSprites.TryGet(ProxyAugmentType, item.type, out sprite)) {
				ownOffset = sprite.BaseOffset;
				return true;
			}
			return false;
		}

		/// <summary>Vanilla's fit for an inventory icon (decompiled <c>ItemSlot.DrawItemIcon</c>: a frame over 32 px is scaled
		/// down to 32).</summary>
		private static float Fit(int w, int h) {
			const float limit = 32f;
			return w > limit || h > limit ? limit / Math.Max(w, h) : 1f;
		}

		public override bool PreDrawInInventory(Item item, SpriteBatch spriteBatch, Vector2 position, Rectangle frame, Color drawColor,
			Color itemColor, Vector2 origin, float scale) {
			if ((!IsProduct && !IsStandIn) || !TrySprite(item, out CombinedSprite sprite, out _)) {
				return true;
			}
			// vanilla passed its own fit for the plain frame: take it out, put the combined sprite's in
			float baseScale = scale / Fit(frame.Width, frame.Height);
			float s = baseScale * Fit(sprite.Width, sprite.Height);
			spriteBatch.Draw(sprite.Texture, position, null, drawColor, 0f, new Vector2(sprite.Width / 2f, sprite.Height / 2f), s, SpriteEffects.None, 0f);
			return false;
		}

		public override bool PreDrawInWorld(Item item, SpriteBatch spriteBatch, Color lightColor, Color alphaColor, ref float rotation,
			ref float scale, int whoAmI) {
			if ((!IsProduct && !IsStandIn) || !TrySprite(item, out CombinedSprite sprite, out _)) {
				return true;
			}
			// vanilla stands the frame on the item's hitbox bottom, centred, turning about its middle (decompiled Main.DrawItem)
			Vector2 centre = new(item.position.X + item.width / 2f, item.position.Y + item.height - sprite.Height * scale / 2f);
			Vector2 at = centre - Main.screenPosition;
			at = new Vector2(MathF.Round(at.X), MathF.Round(at.Y));
			spriteBatch.Draw(sprite.Texture, at, null, item.GetAlpha(lightColor), rotation, new Vector2(sprite.Width / 2f, sprite.Height / 2f),
				scale, SpriteEffects.None, 0f);
			return false;
		}

		/// <summary>A swung blade hits as far as its combined sprite reaches: vanilla sizes the swing's hitbox from the item
		/// type's own texture (decompiled <c>Player.ItemCheck_GetMeleeHitbox</c>), so it is scaled about the hand by the
		/// combined sprite's diagonal over the plain one's (clamped x0.75-x1.5). The owner's client only works out melee
		/// hits, and has the textures.</summary>
		public override void UseItemHitbox(Item item, Player player, ref Rectangle hitbox, ref bool noHitbox) {
			if (!IsProduct || noHitbox || Main.dedServ || !TrySprite(item, out CombinedSprite sprite, out _)) {
				return;
			}
			float plain = MathF.Sqrt(sprite.AugmentSize.X * sprite.AugmentSize.X + sprite.AugmentSize.Y * sprite.AugmentSize.Y);
			float combined = MathF.Sqrt(sprite.Width * sprite.Width + sprite.Height * sprite.Height);
			if (plain <= 0f) {
				return;
			}
			float f = Math.Clamp(combined / plain, 0.75f, 1.5f);
			if (Math.Abs(f - 1f) < 0.02f) {
				return;
			}
			Vector2 hand = player.itemLocation;
			float x0 = hand.X + (hitbox.X - hand.X) * f, y0 = hand.Y + (hitbox.Y - hand.Y) * f;
			hitbox = new Rectangle((int)x0, (int)y0, Math.Max(1, (int)(hitbox.Width * f)), Math.Max(1, (int)(hitbox.Height * f)));
		}
	}
}
