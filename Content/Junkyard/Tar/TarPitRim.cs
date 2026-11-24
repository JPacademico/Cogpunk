using Cogpunk.Content.Junkyard.Generation;
using Microsoft.Xna.Framework;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// The tar pit's walls and floor can't be broken (user, 2026-11-24: "the blocks arround the tar pool should be
	/// unbreakable"): the Polished Metal walls either side of the pool, from the yard's ground down, and the sand and stone
	/// floor under it (<see cref="JunkyardPass"/>: <see cref="JunkyardPass.WallThickness"/> columns on the yard side, the left
	/// wall out to the world's edge, <see cref="JunkyardPass.FloorThickness"/> rows of floor). So the only way down to the
	/// Fundamental Stone on its floor is through the tar (the Missing Bones mount), never round it, and the tar can't be let
	/// out through a hole. Nothing mines, blows up, swaps, hammers or actuates them (vanilla's actuators ask
	/// <c>CanKillTile</c> too, decompiled <c>Wiring.DeActive</c>). The air over the tar and anything built in the pool stay
	/// a player's to change.
	/// <para>D2: the pool's rectangle is world data every side has (<see cref="JunkyardSystem"/> sends it with the world), and
	/// vanilla asks on the mining client and on the server alike. D1: a rectangle test; D0: an empty rectangle (no Junkyard)
	/// protects nothing.</para>
	/// </summary>
	public sealed class TarPitRim : GlobalTile
	{
		/// <summary>A tile of the pit's walls or floor.</summary>
		public static bool IsRim(int i, int j) {
			Rectangle pool = JunkyardSystem.PoolArea;
			if (pool.Width <= 0 || pool.Height <= 0) {
				return false;
			}
			int top = pool.Y - JunkyardPass.PoolDrop;                         // the walls start at the yard's ground
			int bottom = pool.Bottom + JunkyardPass.FloorThickness;           // exclusive
			int right = pool.Right + JunkyardPass.WallThickness;              // exclusive
			if (j < top || j >= bottom || i < 0 || i >= right) {
				return false;
			}
			bool wall = i < pool.X || i >= pool.Right;
			bool floor = j >= pool.Bottom;
			return wall || floor;
		}

		public override bool CanKillTile(int i, int j, int type, ref bool blockDamaged) {
			if (IsRim(i, j)) {
				blockDamaged = false;
				return false;
			}
			return true;
		}

		public override bool CanExplode(int i, int j, int type) => !IsRim(i, j);

		public override bool CanReplace(int i, int j, int type, int tileTypeBeingPlaced) => !IsRim(i, j);

		public override bool Slope(int i, int j, int type) => !IsRim(i, j);
	}
}
