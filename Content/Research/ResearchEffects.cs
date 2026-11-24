using System;
using System.Runtime.CompilerServices;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// "Slimed!"'s debuff on an enemy that touched its player (user, 2026-11-19: "aply slimed effect to enemy upon contact").
	/// Vanilla's own Slimed (<c>BuffID.Slimed</c>) only colours an NPC (decompiled 1.4.4 <c>NPC.UpdateNPC_BuffSetFlags</c>
	/// sets <c>drippingSlime</c>, a tint and drips), so this one shows the same drips and also slows the enemy as vanilla's
	/// slows a player (<see cref="NPCHaste.ApplySlow"/>: half speed; bosses, worms and the like only drip). Vanilla's own
	/// Slimed is left as it is.
	/// <para>D2: vanilla syncs NPC buffs (the touching player's client adds it); the slow runs where the NPC moves.</para>
	/// </summary>
	public class ResearchSlimed : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
		}

		public override void Update(NPC npc, ref int buffIndex) {
			npc.drippingSlime = true;                            // vanilla's tint and drips
			NPCHaste.ApplySlow(npc, 2);                          // refreshed every tick while the debuff lasts
		}
	}

	/// <summary>
	/// "Calcified"'s bone (user, 2026-11-19: "every enemy killed launches a small bone fliyng that deals 40 damage if it hits
	/// another enemy"): thrown up out of the fallen enemy, it arcs down under gravity, breaks on the ground or on the first
	/// other enemy it hits (40 damage, fixed: no class scaling). Spins through <see cref="Spins"/> pre-drawn turns (D4: never
	/// rotated at runtime). D2: the killing player's projectile; D0: finite life, no bones from a bone's kill
	/// (<see cref="ResearchPlayer"/>).
	/// </summary>
	public class CalcifiedBone : CogpunkProjectile
	{
		public const int Spins = 8, Life = 150;
		public const float Gravity = 0.3f, MaxFall = 12f;
		private const int Cell = 14, Stride = 16;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Spins;
		}

		public override void SetDefaults() {
			Projectile.width = 10;
			Projectile.height = 10;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Default;
			Projectile.penetrate = 1;
			Projectile.tileCollide = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
		}

		public override void OnSpawn(IEntitySource source) {
			if (source is EntitySource_OnHit hit && hit.Victim is NPC victim && victim.whoAmI >= 0 && victim.whoAmI < Main.maxNPCs) {
				Projectile.localNPCImmunity[victim.whoAmI] = -1;   // "another enemy": never the one it came out of
			}
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFall);
			Projectile.frameCounter++;
			if (Projectile.frameCounter >= 3) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + (Projectile.velocity.X >= 0f ? 1 : Spins - 1)) % Spins;
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 4; i++) {
				Core.Safety.SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Bone, out _);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Spins - 1) * Stride, Cell, Cell);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Cell * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}

	public sealed class TriggerFingerShot : GlobalProjectile
	{
		private sealed class Volley
		{
			public int Projectiles;
			public bool DealtDamage;
		}

		private static readonly ConditionalWeakTable<EntitySource_ItemUse, Volley> volleys = new();
		private Volley volley;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(Projectile entity, bool lateInstantiation) {
			return lateInstantiation && entity.friendly && !entity.hostile && entity.DamageType.CountsAsClass(DamageClass.Ranged);
		}

		public override void OnSpawn(Projectile projectile, IEntitySource source) {
			if (projectile.owner != Main.myPlayer || projectile.owner >= Main.maxPlayers || projectile.owner < 0) {
				return;
			}
			if (source is EntitySource_ItemUse use && projectile.damage > 0 && use.Item.CountsAsClass(DamageClass.Ranged)
				&& projectile.type != ModContent.ProjectileType<Weapons.BanditsSlash>()
				&& Main.player[projectile.owner].GetModPlayer<ResearchPlayer>().Has(ResearchNodes.TriggerFinger)) {
				volley = volleys.GetValue(use, static _ => new Volley());
			}
			else if (source is EntitySource_Parent { Entity: Projectile parent } && parent.owner == projectile.owner
				&& parent.TryGetGlobalProjectile<TriggerFingerShot>(out var origin)) {
				volley = origin.volley;
			}
			if (volley != null) {
				volley.Projectiles++;
			}
		}

		public override void OnHitNPC(Projectile projectile, NPC target, NPC.HitInfo hit, int damageDone) {
			if (volley != null && damageDone > 0) {
				volley.DealtDamage = true;
			}
		}

		public override void OnKill(Projectile projectile, int timeLeft) {
			if (volley != null && --volley.Projectiles == 0 && !volley.DealtDamage) {
				Main.player[projectile.owner].GetModPlayer<ResearchPlayer>().ShotMissed();
			}
		}
	}
}
