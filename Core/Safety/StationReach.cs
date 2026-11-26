using Microsoft.Xna.Framework;
using Terraria;

namespace Cogpunk.Core.Safety
{
	/// <summary>
	/// Is a modded multi-tile station within a player's reach? Vanilla's own test for an open chest (decompiled 1.4.4
	/// <c>Player.IsInInteractionRangeToMultiTileHitbox</c>) builds its box only for vanilla's chests, dressers, piggy banks and two
	/// more types: for any other tile the box stays empty, so it measures from the world's corner and says "out of reach" at
	/// once. It closed the research window and the Combinator's the tick they opened (user, 2026-11-26: "the menu opens but
	/// closes immediately"). This is the same test on the station's own box: the box's tile nearest the player's centre within
	/// vanilla's reach (<see cref="Player.tileRangeX"/>, <see cref="Player.tileRangeY"/>, plus the tile vanilla adds).
	/// <para>D0: pure arithmetic on the given rectangle, no tile access. D1: no allocation.</para>
	/// </summary>
	public static class StationReach
	{
		/// <summary>True while <paramref name="player"/> can reach the station whose top-left tile is <paramref name="topLeft"/> and
		/// that is <paramref name="widthTiles"/> x <paramref name="heightTiles"/> tiles.</summary>
		public static bool InReach(Player player, Point topLeft, int widthTiles, int heightTiles) {
			Rectangle box = new(topLeft.X * 16, topLeft.Y * 16, widthTiles * 16, heightTiles * 16);
			box.Inflate(-1, -1);
			Point near = box.ClosestPointInRect(player.Center).ToTileCoordinates();
			int x = (int)(player.Center.X / 16f), y = (int)(player.Center.Y / 16f);
			return x >= near.X - Player.tileRangeX && x <= near.X + Player.tileRangeX + 1
				&& y >= near.Y - Player.tileRangeY && y <= near.Y + Player.tileRangeY + 1;
		}
	}
}
