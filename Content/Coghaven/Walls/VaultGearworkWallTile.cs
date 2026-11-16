using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Walls
{
	/// <summary>
	/// Vault Gearwork Wall (2026-11-16): the Jade Vault's back wall (user: "the arena room should be unbreakable"): a hammer
	/// strikes it and nothing happens (<see cref="KillWall"/> fails every hit, decompiled tModLoader 1.4.4
	/// <c>ModWall.KillWall</c>: "Fail determines whether the tile is mined"), no explosion takes it, and it drops nothing.
	/// </summary>
	public class VaultGearworkWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.Copper;
			AddMapEntry(new Color(61, 40, 18));
		}

		public override void KillWall(int i, int j, ref bool fail) {
			fail = true;
		}

		public override bool CanExplode(int i, int j) => false;

		public override bool Drop(int i, int j, ref int type) => false;
	}
}
