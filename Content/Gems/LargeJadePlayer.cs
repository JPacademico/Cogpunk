using Cogpunk.Content.Gems.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems
{
	/// <summary>
	/// The <see cref="LargeJade"/> behaves like vanilla's Capture the Gem gems (decompiled 1.4.4 <c>Player.Update</c>: every
	/// 10 ticks the inventory is checked for a large gem; <c>Player.KillMe</c>: a softcore or journey character drops theirs
	/// where they die, the drop flung a little and not grabbable for 100 ticks; <c>PlayerDrawLayers.DrawPlayer_36_CTG</c>:
	/// it hovers 80 px over the bearer's feet). Vanilla's code checks its own item ids, so jade does it here.
	/// <para>D2: the inventory is synced, so every side sees who carries one and draws it; the drop runs on the dying
	/// player's own client and is synced (<see cref="SafeSpawn.TryDropFromPlayer"/>). D1: a 58-slot scan every 10 ticks per
	/// player, no allocation.</para>
	/// </summary>
	public sealed class LargeJadePlayer : ModPlayer
	{
		public const int CheckInterval = 10;

		/// <summary>True while the player carries a Large Jade (rechecked every <see cref="CheckInterval"/> ticks).</summary>
		public bool Carrying;
		private int clock;

		public override void PostUpdate() {
			if (++clock < CheckInterval) {
				return;
			}
			clock = 0;
			Carrying = Find() >= 0;
		}

		private int Find(int from = 0) {
			int type = ModContent.ItemType<LargeJade>();
			Item[] inventory = Player.inventory;
			int count = System.Math.Min(inventory.Length, 59);
			for (int i = from; i < count; i++) {
				if (inventory[i] != null && inventory[i].type == type && inventory[i].stack > 0) {
					return i;
				}
			}
			return -1;
		}

		public override void Kill(double damage, int hitDirection, bool pvp, PlayerDeathReason damageSource) {
			if (Player.whoAmI != Main.myPlayer || (Player.difficulty != PlayerDifficultyID.SoftCore && Player.difficulty != PlayerDifficultyID.Creative)) {
				return;                                        // mediumcore and hardcore drop everything anyway
			}
			for (int i = Find(); i >= 0; i = Find(i + 1)) {   // at most 59 slots
				Item gem = Player.inventory[i];
				Vector2 fling = new(Main.rand.Next(-20, 21) * 0.2f, Main.rand.Next(-20, 1) * 0.2f);
				if (SafeSpawn.TryDropFromPlayer(Player, gem.type, gem.stack, gem.prefix, fling, 100, out _)) {
					gem.TurnToAir();
				}
			}
			Carrying = false;
		}
	}

	/// <summary>Draws a carried <see cref="LargeJade"/> over its bearer's head, after vanilla's own large gems (higher when
	/// they are there too), its brightness pulsing with vanilla's text pulse; never scaled (D4).</summary>
	public sealed class LargeJadeLayer : PlayerDrawLayer
	{
		private const float Height = 80f, AboveVanilla = 22f;
		private static Asset<Texture2D> gem;

		public override void Load() {
			if (!Main.dedServ) {
				gem = DepthLayers.RequestOptional("Cogpunk/Content/Gems/Items/LargeJade");
			}
		}

		public override void Unload() {
			gem = null;
		}

		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.CaptureTheGem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			return drawInfo.shadow == 0f && drawInfo.drawPlayer.GetModPlayer<LargeJadePlayer>().Carrying;
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (gem?.IsLoaded != true) {
				return;
			}
			Texture2D texture = gem.Value;
			Player player = drawInfo.drawPlayer;
			float lift = Height + ((byte)player.ownedLargeGems > 0 ? AboveVanilla : 0f);
			Vector2 at = new((int)(drawInfo.Position.X - Main.screenPosition.X + player.width / 2), (int)(drawInfo.Position.Y - Main.screenPosition.Y + player.height - lift));
			at -= new Vector2(texture.Width / 2, texture.Height / 2);
			float pulse = 0.75f + 0.25f * (Main.mouseTextColor / 255f);
			drawInfo.DrawDataCache.Add(new DrawData(texture, at, null, Color.White * pulse, 0f, Vector2.Zero, 1f, SpriteEffects.None));
		}
	}
}
