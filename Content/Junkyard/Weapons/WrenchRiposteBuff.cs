using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The Metal Wrench's riposte is ready (a parry landed): the next swing deals x<see cref="WrenchParry.RiposteMultiplier"/>.
	/// <see cref="MetalWrenchPlayer"/> gives it, spends it on the next swing and takes it off when that swing ends, so other
	/// clients (vanilla syncs the buff list) see the sparks of a ready riposte and of the riposte swing
	/// (the weapon's <c>MeleeEffects</c>). A glint of brass now and then at the hand while it waits.
	/// </summary>
	public class WrenchRiposteBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoSave[Type] = true;
			Main.buffNoTimeDisplay[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			if (Main.dedServ || player.itemAnimation > 0 || !Main.rand.NextBool(10) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			Vector2 hand = player.MountedCenter + new Vector2(player.direction * 8f, 2f);
			if (SafeSpawn.TryNewDust(hand - new Vector2(3f), 6, 6, DustID.Enchanted_Gold, out Dust d, 0f, -0.6f, 0, default, 0.8f)) {
				d.noGravity = true;
				d.velocity *= 0.4f;
			}
		}

		public override void ModifyBuffText(ref string buffName, ref string tip, ref int rare) {
			tip = Description.Format(WrenchParry.RiposteMultiplier);
		}
	}
}
