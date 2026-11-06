using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Weapons
{
	/// <summary>
	/// The Sheriff's Revolver's cylinder shown over its holder's head: six chambers in a little arc, a brass round in each
	/// loaded one; while it reloads the rounds go back in one by one as the reload runs. Only for the local player (the
	/// rounds are the owner's, <see cref="SheriffsRevolverPlayer"/>); a draw layer, so nothing runs on a dedicated server.
	/// <para>D4: a 2-frame sprite (a round, an empty chamber) drawn at whole pixels, never scaled. D1: six draws, no
	/// allocation.</para>
	/// </summary>
	public sealed class RevolverCylinderLayer : PlayerDrawLayer
	{
		public const int Size = 8, Stride = 10;
		public const float Spacing = 10f, Rise = 18f;

		private static Asset<Texture2D> rounds;
		private static int revolverType = -1;

		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			const string path = "Cogpunk/Content/OldBrassTown/Weapons/SheriffsRevolver_Round";
			rounds = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
		}

		public override void Unload() {
			rounds = null;
			revolverType = -1;
		}

		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.FrontAccFront);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			if (revolverType < 0) {
				revolverType = ModContent.ItemType<SheriffsRevolver>();
			}
			Player player = drawInfo.drawPlayer;
			return drawInfo.shadow == 0f && player.whoAmI == Main.myPlayer && !player.dead && !player.ghost && player.HeldItem.type == revolverType;
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (rounds?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			SheriffsRevolverPlayer cylinder = player.GetModPlayer<SheriffsRevolverPlayer>();
			int loaded = cylinder.Reloading ? (int)(cylinder.ReloadProgress * SheriffsRevolverPlayer.Chambers) : cylinder.Rounds;
			Vector2 top = player.Top - Main.screenPosition + new Vector2(0f, player.gfxOffY - Rise);
			float mid = (SheriffsRevolverPlayer.Chambers - 1) * 0.5f;
			for (int k = 0; k < SheriffsRevolverPlayer.Chambers; k++) {
				float x = (k - mid) * Spacing;
				float y = MathF.Abs(k - mid) * 2f;                  // a shallow arc, the middle chambers highest
				Vector2 at = new(MathF.Round(top.X + x - Size * 0.5f), MathF.Round(top.Y + y - Size * 0.5f));
				Rectangle source = new(0, (k < loaded ? 0 : 1) * Stride, Size, Size);
				drawInfo.DrawDataCache.Add(new DrawData(rounds.Value, at, source, Color.White * (cylinder.Reloading ? 0.75f : 1f)));
			}
		}
	}
}
