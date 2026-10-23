using System;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	/// <summary>
	/// Trash-Tr0m's world state and its intro camera.
	/// <para><see cref="Downed"/> is a <see cref="WorldFlagSystem"/> flag: saved by name, sent with the world data, set by
	/// <see cref="TrashTr0m.OnKill"/>. Until it is set, the Junkyard Cache stays sealed and touching it summons the boss
	/// (<see cref="TrashTr0mSummon"/>).</para>
	/// <para>Intro camera ("the screen locks"): while a Trash-Tr0m is emerging, every client whose player is within
	/// <see cref="TrashTr0m.CameraLockRange"/> eases its view onto the boss, holds it there and eases back
	/// (<see cref="TrashTr0m.CameraLock"/>). The boss's state and timer are synced <c>ai[]</c> values, so every client
	/// replays the same intro, including one that joins halfway (D2). Client only; one NPC lookup per frame (D1).</para>
	/// </summary>
	public sealed class TrashTr0mSystem : ModSystem
	{
		public const string DownedFlagName = "DownedTrashTr0m";

		private static int downedFlag = -1;
		private static int introNpc = -1;

		public static bool Downed => WorldFlagSystem.Get(downedFlag);

		public static ref bool DownedFlag => ref WorldFlagSystem.Flag(downedFlag);

		public override void Load() {
			downedFlag = WorldFlagSystem.Register(DownedFlagName);
		}

		public override void Unload() {
			downedFlag = -1;
			introNpc = -1;
		}

		public override void OnWorldUnload() {
			introNpc = -1;
			TrashTr0mSummon.ResetCooldown();
		}

		/// <summary>Called by an emerging Trash-Tr0m on clients, every tick, so the camera knows whom to follow.</summary>
		internal static void TrackIntro(int whoAmI) {
			introNpc = whoAmI;
		}

		public override void ModifyScreenPosition() {
			if (Main.dedServ || Main.gameMenu || introNpc < 0) {
				return;
			}
			NPC npc = Main.npc[introNpc];
			if (!npc.active || npc.ModNPC is not TrashTr0m boss) {
				introNpc = -1;
				return;
			}
			float lockAmount = boss.CameraLock(Main.LocalPlayer);
			if (lockAmount <= 0f) {
				if (!boss.IsEmerging) {
					introNpc = -1;
				}
				return;
			}
			Vector2 focus = boss.CameraFocus - new Vector2(Main.screenWidth, Main.screenHeight) * 0.5f;
			float eased = lockAmount * lockAmount * (3f - 2f * lockAmount);     // smoothstep
			Main.screenPosition = Vector2.Lerp(Main.screenPosition, focus, eased);
			Main.screenPosition = new Vector2(MathF.Round(Main.screenPosition.X), MathF.Round(Main.screenPosition.Y));
		}
	}
}
