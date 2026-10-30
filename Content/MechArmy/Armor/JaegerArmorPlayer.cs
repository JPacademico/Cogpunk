using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Armor
{
	/// <summary>
	/// Jaeger armor effects that need per-player state (user-set 2026-10-28):
	/// <list type="bullet">
	/// <item><b>Chestplate:</b> contact damage taken x <see cref="ContactDamageTaken"/> (hits from NPC bodies only,
	/// <see cref="ModifyHitByNPC"/>; projectiles are untouched).</item>
	/// <item><b>Set bonus, the ram:</b> every enemy the wearer's hitbox touches takes <see cref="RamDamage"/> melee damage
	/// (scaled by the wearer's melee damage, rolling melee crit, knockback <see cref="RamKnockback"/> scaled by the set's
	/// knockback bonus), at most once every <see cref="RamCooldown"/> ticks per enemy. The wearer still takes the enemy's
	/// contact hit as usual (knockback immunity keeps them standing).</item>
	/// </list>
	/// <para>D2: the ram runs on the wearer's client (like a melee swing) through vanilla's
	/// <see cref="Player.ApplyDamageToNPC"/>, which calls the hit hooks and sends the strike (decompiled
	/// <c>Player.StrikeNPCDirect</c>: <c>NetMessage.SendStrikeNPC</c>). D1: one pass over the active NPCs per tick while the
	/// set is worn, a per-NPC tick stamp (allocated once per player in <see cref="Initialize"/>), no allocation per tick.</para>
	/// </summary>
	public sealed class JaegerArmorPlayer : ModPlayer
	{
		public const int RamDamage = 70;                // melee, user-set
		public const float RamKnockback = 7f;
		public const int RamCooldown = 30;              // ticks between rams on the same enemy (my call)

		public bool Ram;
		public float ContactDamageTaken = 1f;

		private uint[] lastRam;

		public override void Initialize() {
			lastRam = new uint[Main.maxNPCs];
		}

		public override void ResetEffects() {
			Ram = false;
			ContactDamageTaken = 1f;
		}

		public override void ModifyHitByNPC(NPC npc, ref Player.HurtModifiers modifiers) {
			if (ContactDamageTaken != 1f) {
				modifiers.FinalDamage *= MathHelper.Max(0f, ContactDamageTaken);
			}
		}

		public override void PostUpdate() {
			if (!Ram || Player.whoAmI != Main.myPlayer || Player.dead || lastRam == null) {
				return;
			}
			Rectangle body = Player.Hitbox;
			uint now = Main.GameUpdateCount;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.whoAmI >= lastRam.Length || !CanRam(npc) || !body.Intersects(npc.Hitbox)) {
					continue;
				}
				if (lastRam[npc.whoAmI] != 0 && now - lastRam[npc.whoAmI] < RamCooldown) {
					continue;
				}
				lastRam[npc.whoAmI] = now == 0 ? 1u : now;
				int damage = (int)Player.GetTotalDamage(DamageClass.Melee).ApplyTo(RamDamage);
				float knockback = Player.GetTotalKnockback(DamageClass.Melee).ApplyTo(RamKnockback);
				bool crit = Main.rand.Next(100) < Player.GetTotalCritChance(DamageClass.Melee);
				int direction = npc.Center.X >= Player.Center.X ? 1 : -1;
				Player.ApplyDamageToNPC(npc, damage, knockback, direction, crit, DamageClass.Melee);
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.5f, Volume = 0.7f }, npc.Center);
					for (int i = 0; i < 5; i++) {
						SafeSpawn.TryNewDust(Vector2.Lerp(Player.Center, npc.Center, 0.5f) - new Vector2(6f), 12, 12, DustID.Iron, out _);
					}
				}
			}
		}

		private bool CanRam(NPC npc) {
			return !npc.friendly && !npc.townNPC && !npc.dontTakeDamage && npc.lifeMax > 5 && !NPCID.Sets.CountsAsCritter[npc.type]
				&& Player.CanNPCBeHitByPlayerOrPlayerProjectile(npc);
		}
	}
}
