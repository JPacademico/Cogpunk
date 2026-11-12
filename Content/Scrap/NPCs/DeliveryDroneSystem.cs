using System;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.NPCs
{
	/// <summary>
	/// Sends the <see cref="DeliveryDrone"/> (the Amazonian Drone until 2026-11-11) (user-set 2026-11-10b: "can spawn anywhere when there are dropped items or coins
	/// on the ground for more than 20 seconds"; "rare"). Once a second (<see cref="CheckInterval"/>) the server looks for an
	/// item that has lain on the ground <see cref="LyingTicks"/> (vanilla's own <c>Item.timeSinceItemSpawned</c>) within
	/// <see cref="NearX"/> x <see cref="NearY"/> of a living player (so the theft is seen: anywhere in the world, any biome
	/// or layer), and with one found, 1 time in <see cref="SpawnOneIn"/> a drone comes for it, from just off screen beyond
	/// it, high up. One drone at a time, and none for <see cref="CooldownTicks"/> after one comes (my calls: about 40 s on
	/// average after the 20, then a minute's rest). Never while a boss is alive (my call: no theft in a boss fight).
	/// <para>What it takes (<see cref="CanSteal"/>): anything a player could pick up, coins too, but not hearts, mana stars
	/// and the like (they aren't items to keep), treasure bags (a boss's reward) or quest fish, and nothing a player is
	/// already pulling in.</para>
	/// <para>D2: server or singleplayer only (<c>PostUpdateWorld</c>); the NPC is spawned there and synced by vanilla. D0:
	/// spawned through <see cref="SafeSpawn"/> (its reserve slots respected), the spot clamped inside the world. D1: one pass
	/// over the 400 items a second, no allocation.</para>
	/// </summary>
	public sealed class DeliveryDroneSystem : ModSystem
	{
		public const int CheckInterval = 60;
		public const int LyingTicks = 20 * 60;                          // user-set: 20 s on the ground
		public const int SpawnOneIn = 40;                               // my call
		public const int CooldownTicks = 60 * 60;                       // my call: a minute between drones
		public const float NearX = 1400f, NearY = 900f;                 // the item this near a player (a little past the screen)
		public const float SpawnBeyond = 1100f, SpawnAbove = 300f;      // the drone appears this far off, past the item, and up

		private static int timer, cooldown;

		public override void ClearWorld() {
			timer = 0;
			cooldown = 0;
		}

		/// <summary>An item the drone can take: lying in the world for <paramref name="lying"/> ticks or more, not a pickup
		/// (hearts, stars), not a treasure bag, not a quest fish, not being pulled in by a player.</summary>
		public static bool CanSteal(Item item, int lying) {
			return item != null && item.active && !item.IsAir && item.stack > 0 && item.type > ItemID.None && item.type < ItemLoader.ItemCount
				&& item.timeSinceItemSpawned >= lying && !item.beingGrabbed && !item.instanced && !item.questItem
				&& !ItemID.Sets.IsAPickup[item.type] && !ItemID.Sets.BossBag[item.type];
		}

		public override void PostUpdateWorld() {
			if (cooldown > 0) {
				cooldown--;
				return;
			}
			if (++timer < CheckInterval) {
				return;
			}
			timer = 0;
			int type = ModContent.NPCType<DeliveryDrone>();
			if (NPC.AnyNPCs(type) || AnyBoss()) {
				return;
			}
			int found = FindLyingItem(out Player near);
			if (found < 0 || near == null || !Main.rand.NextBool(SpawnOneIn)) {
				return;
			}
			Item item = Main.item[found];
			int side = item.Center.X >= near.Center.X ? 1 : -1;                // from beyond the item, away from the player
			float x = MathHelper.Clamp(item.Center.X + side * SpawnBeyond, 50f * 16f, (Main.maxTilesX - 50) * 16f);
			float y = MathHelper.Clamp(item.Center.Y - SpawnAbove, 50f * 16f, (Main.maxTilesY - 50) * 16f);
			if (SafeSpawn.TryNewNPC(Entity.GetSource_NaturalSpawn(), (int)x, (int)y, type, out NPC drone, ai2: found + 1)) {
				drone.direction = drone.spriteDirection = -side;
				cooldown = CooldownTicks;
			}
		}

		private static bool AnyBoss() {
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.boss) {
					return true;
				}
			}
			return false;
		}

		/// <summary>The first item (from a random start, so no slot is favoured) that has lain long enough near a living
		/// player, and that player; -1 if none.</summary>
		private static int FindLyingItem(out Player near) {
			near = null;
			int start = Main.rand.Next(Main.maxItems);
			for (int k = 0; k < Main.maxItems; k++) {
				int i = (start + k) % Main.maxItems;
				Item item = Main.item[i];
				if (!CanSteal(item, LyingTicks)) {
					continue;
				}
				foreach (Player player in Main.ActivePlayers) {
					if (player.dead) {
						continue;
					}
					Vector2 d = item.Center - player.Center;
					if (Math.Abs(d.X) < NearX && Math.Abs(d.Y) < NearY) {
						near = player;
						return i;
					}
				}
			}
			return -1;
		}
	}
}
