using System.Collections.Generic;
using Cogpunk.Core.Systems;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Items
{
	/// <summary>
	/// The <see cref="BottleOfLostSouls"/>' effect: the wearer's minions and sentries (and their shots) can land critical
	/// strikes. vanilla never rolls one for summon damage (decompiled <c>Projectile.Damage</c>: <c>if
	/// (DamageType.UseStandardCritCalcs &amp;&amp; Main.rand.Next(100) &lt; CritChance)</c>), so this rolls the projectile's own
	/// <c>CritChance</c> (kept current for minions and sentries by tModLoader, inherited by their shots) in
	/// <see cref="ModifyHitNPCWithProj"/>. Projectiles in <see cref="CogpunkSets.RollsOwnCrit"/> (Cogpunk's own minions) are
	/// skipped: they already roll it.
	/// <para>D2: friendly projectile hits are computed by the owner's client (that is where this hook runs), which rolls with
	/// its own random and sends the strike, crit included, as usual. D1: a flag and a few field reads per hit; no allocation.</para>
	/// </summary>
	public sealed class LostSoulsPlayer : ModPlayer
	{
		public bool MinionCrits;

		public override void ResetEffects() {
			MinionCrits = false;
		}

		/// <summary>A projectile this effect rolls for: a minion or sentry (or one's shot) dealing damage that vanilla never
		/// crits, not one that rolls for itself.</summary>
		public static bool Applies(Projectile proj) {
			return proj.IsMinionOrSentryRelated && !proj.DamageType.UseStandardCritCalcs && !CogpunkSets.RollsOwnCritType(proj.type);
		}

		public override void ModifyHitNPCWithProj(Projectile proj, NPC target, ref NPC.HitModifiers modifiers) {
			if (MinionCrits && Applies(proj) && Main.rand.Next(100) < proj.CritChance) {
				modifiers.SetCrit();
			}
		}
	}

	/// <summary>Shows the critical strike chance on summon weapons while the <see cref="BottleOfLostSouls"/> is worn (vanilla
	/// hides the line for summon damage), the way Cogpunk's own summon items always show it. Tooltips only (no hot path).</summary>
	public sealed class LostSoulsTooltip : GlobalItem
	{
		public override bool AppliesToEntity(Item entity, bool lateInstantiation) {
			// lateInstantiation: called again after SetDefaults, when the item's class and projectile are known
			return lateInstantiation && entity.shoot > ProjectileID.None && entity.CountsAsClass(DamageClass.Summon)
				&& !entity.CountsAsClass(DamageClass.SummonMeleeSpeed);
		}

		public override void ModifyTooltips(Item item, List<TooltipLine> tooltips) {
			Player player = Main.LocalPlayer;
			if (player == null || !player.GetModPlayer<LostSoulsPlayer>().MinionCrits || item.damage <= 0) {
				return;
			}
			for (int i = 0; i < tooltips.Count; i++) {
				if (tooltips[i].Name == "CritChance") {
					return;                             // already shown (Cogpunk's own summon items add it themselves, before globals)
				}
			}
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Damage");
			if (index < 0) {
				return;
			}
			int crit = player.GetWeaponCrit(item);
			tooltips.Insert(index + 1, new TooltipLine(Mod, "CritChance", crit + Lang.tip[41].Value));
		}
	}
}
