using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy
{
	/// <summary>
	/// Death gores of the Mech Army (<c>Content/MechArmy/Gores/</c>, autoloaded by tModLoader). Clients only (D1); a missing
	/// gore is skipped (D0). Up to three per call, no <c>params</c> array (D1).
	/// </summary>
	public static class MechArmyGores
	{
		public static void Spawn(NPC npc, string a, string b = null, string c = null) {
			if (Main.dedServ) {
				return;
			}
			One(npc, a);
			One(npc, b);
			One(npc, c);
		}

		private static void One(NPC npc, string name) {
			if (name == null || !ModContent.GetInstance<CogpunkMod>().TryFind(name, out ModGore gore)) {
				return;
			}
			SafeSpawn.TryNewGore(npc.GetSource_Death(), npc.position + new Microsoft.Xna.Framework.Vector2(Main.rand.Next(npc.width), Main.rand.Next(npc.height)),
				npc.velocity * 0.5f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
		}
	}
}
