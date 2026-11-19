using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// The Jade-shaper Whip's tag (ExampleMod 1.4.4 <c>ExampleWhipDebuff</c>): minions and sentries hitting a tagged enemy deal
	/// <see cref="TagDamage"/> more, one over the best pre-Hardmode tag (decompiled 1.4.4 <c>Projectile.Damage</c>: buff 326, the
	/// Spinal Tap's, adds 7; 315 the Snapthorn's 6; 307 the Leather Whip's 4). Vanilla's 240 ticks; synced by vanilla from
	/// <c>NPC.AddBuff</c> on the owner's client.
	/// </summary>
	public class JadeShaperWhipDebuff : CogpunkBuff
	{
		public const int TagDamage = 8;
		public const int TagTicks = 240;

		public override void SetStaticDefaults() {
			BuffID.Sets.IsATagBuff[Type] = true;
		}
	}

	/// <summary>Adds <see cref="JadeShaperWhipDebuff.TagDamage"/> to minion and sentry hits on a tagged enemy (ExampleMod 1.4.4
	/// <c>ExampleWhipDebuffNPC</c>). Per hit, not per tick (D1); no per-entity data, so no instancing.</summary>
	public sealed class JadeShaperWhipDebuffNPC : GlobalNPC
	{
		// Any NPC can be tagged, so this can't be narrowed by type.
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => true;

		public override void ModifyHitByProjectile(NPC npc, Projectile projectile, ref NPC.HitModifiers modifiers) {
			if (projectile.npcProj || projectile.trap || !projectile.IsMinionOrSentryRelated) {
				return;
			}
			if (npc.HasBuff<JadeShaperWhipDebuff>()) {
				modifiers.FlatBonusDamage += JadeShaperWhipDebuff.TagDamage * ProjectileID.Sets.SummonTagDamageMultiplier[projectile.type];
			}
		}
	}
}
