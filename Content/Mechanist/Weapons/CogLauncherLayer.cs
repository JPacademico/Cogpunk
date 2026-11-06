using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// The <see cref="CogLauncher"/> in its holder's hands while it fires (it is <c>noUseGraphic</c>, so vanilla draws nothing):
	/// the piston's frames from <c>CogLauncher_Held.png</c> (art/mechanist/make_cog_launcher_art.py), picked from how far the use
	/// has run: <see cref="FiredFrame"/> (the ram punched forward through the empty cup) for the first
	/// <see cref="FiredUntil"/> of it, then <see cref="ReturnFrame"/> (the ram halfway back, the next cog dropping in) until
	/// <see cref="ReturnUntil"/>, then <see cref="LoadedFrame"/> (the item sprite: a cog clocked in, the ram behind it).
	/// <para>Placed exactly as vanilla places a gun (decompiled <c>PlayerDrawLayers.DrawPlayer_27_HeldItem</c>, useStyle 5:
	/// drawn at <c>ItemLocation + (0, H/2 + gravDir * HoldoutOffset.Y)</c>, origin <c>(-HoldoutOffset.X, H/2)</c>, or
	/// <c>(W + HoldoutOffset.X, H/2)</c> facing left, turned by <c>itemRotation</c>, the item's scale and flip; and
	/// <c>Main.DrawPlayerItemPos</c>: the offset's X is the mod's own), in the same slot as the held item, so the arm still
	/// covers its grip.</para>
	/// <para>D2: every client draws every player's from their synced use (itemAnimation, itemRotation); nothing is sent.
	/// D1: one draw, no allocation. D0: a draw layer never runs on a dedicated server; a missing sheet draws nothing.</para>
	/// </summary>
	public sealed class CogLauncherLayer : PlayerDrawLayer
	{
		public const int FrameWidth = 60, FrameHeight = 32, Stride = FrameHeight + 2;
		public const int FiredFrame = 0, ReturnFrame = 1, LoadedFrame = 2;
		public const float FiredUntil = 0.25f, ReturnUntil = 0.55f;

		private static Asset<Texture2D> held;
		private static int launcherType = -1;

		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			const string path = "Cogpunk/Content/Mechanist/Weapons/CogLauncher_Held";
			held = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
		}

		public override void Unload() {
			held = null;
			launcherType = -1;
		}

		public override Position GetDefaultPosition() => new AfterParent(PlayerDrawLayers.HeldItem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			if (launcherType < 0) {
				launcherType = ModContent.ItemType<CogLauncher>();
			}
			Player player = drawInfo.drawPlayer;
			return drawInfo.shadow == 0f && player.itemAnimation > 0 && player.HeldItem.type == launcherType && !player.dead && !player.frozen
				&& !player.JustDroppedAnItem;
		}

		/// <summary>The frame for <paramref name="player"/>'s use so far (every side reads the same synced numbers).</summary>
		public static int FrameFor(Player player) {
			float done = 1f - player.itemAnimation / (float)Math.Max(1, player.itemAnimationMax);
			return done < FiredUntil ? FiredFrame : done < ReturnUntil ? ReturnFrame : LoadedFrame;
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (held?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			Texture2D texture = held.Value;
			Rectangle source = new(0, FrameFor(player) * Stride, FrameWidth, FrameHeight);
			if (source.Bottom > texture.Height) {
				return;
			}
			int back = (int)CogLauncher.Holdout.X;
			float offsetY = FrameHeight / 2 + player.gravDir * CogLauncher.Holdout.Y;
			Vector2 origin = player.direction == -1 ? new Vector2(FrameWidth + back, FrameHeight / 2) : new Vector2(-back, FrameHeight / 2);
			Vector2 at = new((int)(drawInfo.ItemLocation.X - Main.screenPosition.X), (int)(drawInfo.ItemLocation.Y - Main.screenPosition.Y + offsetY));
			Color light = Lighting.GetColor((int)((drawInfo.Position.X + player.width * 0.5f) / 16f), (int)((drawInfo.Position.Y + player.height * 0.5f) / 16f));
			drawInfo.DrawDataCache.Add(new DrawData(texture, at, source, player.HeldItem.GetAlpha(light), player.itemRotation, origin,
				player.GetAdjustedItemScale(player.HeldItem), drawInfo.itemEffect));
		}
	}
}
