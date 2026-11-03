using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The Tar Whip's tag (ExampleMod 1.4.4 <c>ExampleWhipDebuff</c>): minions and sentries hitting a tagged enemy deal
	/// <see cref="TagDamage"/> more, the Spinal Tap's (decompiled 1.4.4 <c>Projectile.Damage</c>: buff 326 adds 7). Applied
	/// for 240 ticks by every lash (vanilla's tag time), synced by vanilla from <c>NPC.AddBuff</c> on the owner's client.
	/// </summary>
	public class TarWhipDebuff : CogpunkBuff
	{
		public const int TagDamage = 7;
		public const int TagTicks = 240;

		public override void SetStaticDefaults() {
			BuffID.Sets.IsATagBuff[Type] = true;           // reaches enemies immune to every other debuff, like vanilla's tags
		}
	}

	/// <summary>Adds <see cref="TarWhipDebuff.TagDamage"/> to minion and sentry hits on a tagged enemy (ExampleMod 1.4.4
	/// <c>ExampleWhipDebuffNPC</c>). Per hit, not per tick (D1); no per-entity data, so no instancing.</summary>
	public sealed class TarWhipDebuffNPC : GlobalNPC
	{
		// Any NPC can be tagged, so this can't be narrowed by type.
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => true;

		public override void ModifyHitByProjectile(NPC npc, Projectile projectile, ref NPC.HitModifiers modifiers) {
			// only player attacks benefit (the NPC and trap checks), and only minions and sentries (a whip's tag)
			if (projectile.npcProj || projectile.trap || !projectile.IsMinionOrSentryRelated) {
				return;
			}
			if (npc.HasBuff<TarWhipDebuff>()) {
				modifiers.FlatBonusDamage += TarWhipDebuff.TagDamage * ProjectileID.Sets.SummonTagDamageMultiplier[projectile.type];
			}
		}
	}
}
