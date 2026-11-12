using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Safety
{
	/// <summary>
	/// The only way Cogpunk code spawns NPCs, projectiles, dust and items (D0).
	/// Vanilla behaviour when the arrays are full (verified by decompiling tModLoader v2026.08.3.0):
	/// <list type="bullet">
	/// <item><c>Projectile.NewProjectile</c> never fails: it silently <b>overwrites the oldest projectile</b> (1000 slots).</item>
	/// <item><c>NPC.NewNPC</c> returns 200, <c>Dust.NewDust</c> 6000, <c>Item.NewItem</c> 400: dummy slots past the real arrays.</item>
	/// <item>An invalid type id makes SetDefaults index out of range and crashes.</item>
	/// </list>
	/// Every method here returns <c>false</c> instead of misbehaving, and keeps a reserve of slots free for vanilla and other mods.
	/// </summary>
	public static class SafeSpawn
	{
		/// <summary>Projectile slots Cogpunk never fills unless the spawn is marked critical.</summary>
		public const int ProjectileReserve = 100;

		/// <summary>NPC slots Cogpunk never fills unless the spawn is marked critical.</summary>
		public const int NPCReserve = 20;

		/// <summary>
		/// Spawns an NPC. <b>Server or singleplayer only</b> (D2); syncs it to clients on the server.
		/// <paramref name="x"/> is the horizontal center and <paramref name="y"/> the bottom, as in <c>NPC.NewNPC</c>.
		/// Use <paramref name="critical"/> only for spawns that must happen (a boss itself), never for minion waves.
		/// </summary>
		public static bool TryNewNPC(IEntitySource source, int x, int y, int type, out NPC npc, int start = 0,
			float ai0 = 0f, float ai1 = 0f, float ai2 = 0f, float ai3 = 0f, int target = 255, bool critical = false) {
			npc = null;
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				SafeLog.Warn("Spawn.NPC.OnClient", "Refused an NPC spawn on a multiplayer client; NPCs must be spawned by the server.");
				return false;
			}
			if (type <= NPCID.None || type >= NPCLoader.NPCCount) {
				SafeLog.Warn("Spawn.NPC.BadType", "Refused NPC spawn with invalid type {0}.", type);
				return false;
			}
			int free = SpawnBudgetSystem.FreeNPCSlots;
			if (free <= 0 || (!critical && free <= NPCReserve)) {
				SafeLog.Warn("Spawn.NPC.Budget", "NPC spawn refused: the NPC array is (nearly) full.");
				return false;
			}

			int index = NPC.NewNPC(source, x, y, type, start, ai0, ai1, ai2, ai3, target);
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			SpawnBudgetSystem.FreeNPCSlots = free - 1;
			npc = Main.npc[index];
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: index);
			}
			return true;
		}

		/// <summary>
		/// Spawns a projectile without ever overwriting an existing one.
		/// Hostile projectiles: call on the server or in singleplayer. Player projectiles: call on the owner's client.
		/// </summary>
		public static bool TryNewProjectile(IEntitySource source, Vector2 position, Vector2 velocity, int type, int damage,
			float knockback, out Projectile projectile, int owner = -1, float ai0 = 0f, float ai1 = 0f, float ai2 = 0f, bool critical = false) {
			projectile = null;
			if (type <= ProjectileID.None || type >= ProjectileLoader.ProjectileCount) {
				SafeLog.Warn("Spawn.Projectile.BadType", "Refused projectile spawn with invalid type {0}.", type);
				return false;
			}
			if (!MathSafety.IsFinite(position) || !MathSafety.IsFinite(velocity)) {
				SafeLog.Warn("Spawn.Projectile.NaN", "Refused projectile spawn with a NaN/Infinity position or velocity.");
				return false;
			}
			int free = SpawnBudgetSystem.FreeProjectileSlots;
			if (free <= 0 || (!critical && free <= ProjectileReserve)) {
				SafeLog.Warn("Spawn.Projectile.Budget", "Projectile spawn refused: the projectile array is (nearly) full.");
				return false;
			}

			int index = Projectile.NewProjectile(source, position, velocity, type, damage, knockback, owner, ai0, ai1, ai2);
			if (index < 0 || index >= Main.maxProjectiles) {
				return false;
			}
			SpawnBudgetSystem.FreeProjectileSlots = free - 1;
			projectile = Main.projectile[index];
			return true;
		}

		/// <summary>Spawns dust. Always <c>false</c> on a dedicated server (dust is visual only, D1).</summary>
		public static bool TryNewDust(Vector2 position, int width, int height, int type, out Dust dust,
			float speedX = 0f, float speedY = 0f, int alpha = 0, Color color = default, float scale = 1f) {
			dust = null;
			if (Main.dedServ) {
				return false;
			}
			int index = Dust.NewDust(position, width, height, type, speedX, speedY, alpha, color, scale);
			if (index < 0 || index >= Main.maxDust) {
				return false;
			}
			dust = Main.dust[index];
			return true;
		}

		/// <summary>
		/// Spawns one dust puff of the tile at (<paramref name="x"/>, <paramref name="y"/>), using the dust vanilla picks for
		/// that tile when it is hit (<c>WorldGen.KillTile_MakeTileDust</c>: every vanilla tile plus <c>ModTile.DustType</c>;
		/// it only makes dust, the tile is not touched). Client-side visual: always <c>false</c> on a dedicated server, for
		/// coordinates outside the world, or for an empty tile.
		/// </summary>
		public static bool TryTileDust(int x, int y) {
			if (Main.dedServ || !TileSafety.TryGetTile(x, y, out Tile tile) || !tile.HasTile) {
				return false;
			}
			int index = WorldGen.KillTile_MakeTileDust(x, y, tile);
			return index >= 0 && index < Main.maxDust;
		}

		/// <summary>Spawns gore. Always <c>false</c> on a dedicated server (gore is visual only, D1).</summary>
		public static bool TryNewGore(IEntitySource source, Vector2 position, Vector2 velocity, int type, out Gore gore, float scale = 1f) {
			gore = null;
			if (Main.dedServ) {
				return false;
			}
			if (type <= 0 || type >= GoreLoader.GoreCount) {
				SafeLog.Warn("Spawn.Gore.BadType", "Refused gore spawn with invalid type {0}.", type);
				return false;
			}
			int index = Gore.NewGore(source, position, velocity, type, scale);
			if (index < 0 || index >= Main.maxGore) {
				return false;
			}
			gore = Main.gore[index];
			return true;
		}

		/// <summary>
		/// Drops an item into the world from server-side logic (NPC/tile/world code). <b>Server or singleplayer only.</b>
		/// To give an item directly to a player, use <c>player.QuickSpawnItem</c> instead.
		/// </summary>
		public static bool TryNewItem(IEntitySource source, Rectangle area, int type, int stack, out Item item) {
			item = null;
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				SafeLog.Warn("Spawn.Item.OnClient", "Refused a world item drop on a multiplayer client; drops must come from the server.");
				return false;
			}
			if (type <= ItemID.None || type >= ItemLoader.ItemCount || stack <= 0) {
				SafeLog.Warn("Spawn.Item.BadType", "Refused item drop with invalid type {0} or stack {1}.", type, stack);
				return false;
			}
			int index = Item.NewItem(source, area.X, area.Y, area.Width, area.Height, type, stack);
			if (index < 0 || index >= Main.maxItems) {
				return false;
			}
			item = Main.item[index];
			return true;
		}

		/// <summary>
		/// A copy of <paramref name="template"/> dropped in <paramref name="area"/>, its stack, prefix and modded data kept
		/// (vanilla's <c>Item.NewItem(source, x, y, w, h, Item)</c>): what a thief gives back (the Delivery Drone, 2026-11-10b).
		/// Server or singleplayer only, like every world drop.
		/// </summary>
		public static bool TryNewItem(IEntitySource source, Rectangle area, Item template, out Item item) {
			item = null;
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				SafeLog.Warn("Spawn.Item.OnClient", "Refused a world item drop on a multiplayer client; drops must come from the server.");
				return false;
			}
			if (template == null || template.IsAir || template.type <= ItemID.None || template.type >= ItemLoader.ItemCount || template.stack <= 0) {
				SafeLog.Warn("Spawn.Item.BadTemplate", "Refused an item drop copied from an empty or invalid item.");
				return false;
			}
			int index = Item.NewItem(source, area.X, area.Y, area.Width, area.Height, template);
			if (index < 0 || index >= Main.maxItems) {
				return false;
			}
			item = Main.item[index];
			return true;
		}

		/// <summary>
		/// The local player throws one of their own items into the world, as vanilla does on the dying player's client for
		/// the large gems of Capture the Gem (decompiled <c>Player.KillMe</c>: <c>Item.NewItem</c> there, then message 21 from
		/// a multiplayer client). <b>Only for <see cref="Main.myPlayer"/></b>; the item is synced by this call.
		/// </summary>
		public static bool TryDropFromPlayer(Player owner, int type, int stack, int prefix, Vector2 velocity, int noGrabDelay, out Item item) {
			item = null;
			if (owner == null || owner.whoAmI != Main.myPlayer || Main.netMode == NetmodeID.Server) {
				SafeLog.Warn("Spawn.PlayerDrop.NotOwner", "Refused a player drop that isn't the local player's own.");
				return false;
			}
			if (type <= ItemID.None || type >= ItemLoader.ItemCount || stack <= 0) {
				SafeLog.Warn("Spawn.PlayerDrop.BadType", "Refused player drop with invalid type {0} or stack {1}.", type, stack);
				return false;
			}
			int index = Item.NewItem(owner.GetSource_Death(), (int)owner.position.X, (int)owner.position.Y, owner.width, owner.height, type, stack, false,
				prefix);
			if (index < 0 || index >= Main.maxItems) {
				return false;
			}
			item = Main.item[index];
			if (MathSafety.IsFinite(velocity)) {
				item.velocity = velocity;
			}
			item.noGrabDelay = noGrabDelay;
			item.favorited = false;
			item.newAndShiny = false;
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				NetMessage.SendData(MessageID.SyncItem, -1, -1, null, index);
			}
			return true;
		}
	}
}
