using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Buffs
{
	/// <summary>
	/// The Conductor's Curse (user-set 2026-11-05: "a cursed projectile that if it hits a player curses it for 6 seconds;
	/// a cursed player takes 25% more damage from the train and the ghosts"): given by his lantern's bolts
	/// (<see cref="Projectiles.ConductorFlame"/>) for <see cref="Ticks"/>; while it lasts the ghost train and his ghosts hit
	/// for <see cref="DamageTaken"/>x (<see cref="Amplify"/>, applied by them). A modded debuff is not in vanilla's
	/// <c>LongerExpertDebuff</c> set, so its 6 s are 6 s in every mode (D3 rule 8).
	/// <para>D2: added on the hit player's own client (where hostile hits are decided), synced by vanilla's buff sync.
	/// D1: a ghost-green mote now and then, clients only.</para>
	/// </summary>
	public class ConductorCurse : CogpunkBuff
	{
		public const int Ticks = 360;                   // 6 s (user-set)
		public const float DamageTaken = 1.25f;         // user-set

		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			if (!Main.dedServ && Main.rand.NextBool(8) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(player.position, player.width, player.height, DustID.CursedTorch, out Dust d)) {
				d.noGravity = true;
				d.velocity = new Vector2(Main.rand.NextFloat(-0.4f, 0.4f), -Main.rand.NextFloat(0.6f, 1.4f));
				d.scale = 0.9f;
			}
		}

		/// <summary>A hit on <paramref name="target"/> from the train or a ghost: +25% while cursed.</summary>
		public static void Amplify(Player target, ref Player.HurtModifiers modifiers) {
			if (target.HasBuff(ModContent.BuffType<ConductorCurse>())) {
				modifiers.FinalDamage *= DamageTaken;
			}
		}
	}
}
