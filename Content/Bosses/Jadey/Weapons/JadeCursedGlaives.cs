using System.Collections.Generic;
using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// Jade Cursed Glaives (Glaives Amaldiçoadas de Jade), one of Jadey's three weapons (user-set 2026-11-17: "melee weapon with
	/// fast use time that perform mid range (grass blade range) diagonal stylized slashes (ensure cool crossing diagonal slash
	/// animation, perspective techniques) and apply jade curse, on right mouse it should throw the glaive up to 18 tiles dealing
	/// damage and returning (like a boomerang, pierces one enemy only and hits on the way back as well) deals bonus damage to
	/// jade petrified enemies (50%). it should look like the image example"; then, the same day: one glaive with the blades parted
	/// in its middle, "+3 tiles" of range, the 50% on the slashes too, 27 damage with 12% crit). A pair of glaives, each one
	/// weapon: two long jade blades sweeping out from a gilt shield guard and curling up into points (the user's reference,
	/// redrawn in Cogpunk's jade, gilt and steel).
	/// <list type="bullet">
	/// <item>Left click: a diagonal slash (<see cref="JadeGlaiveSlash"/>), the glaives taking turns, one down-and-across (""),
	/// the other up-and-across ("/"), so two slashes cross in an X in front of the wielder; a jade wave runs ahead of the blade to
	/// 3 tiles past the Blade of Grass's reach (the hits reach as far); each hit adds a jade curse stack
	/// (<see cref="Gems.JadeCurseNPC.Hit"/>; three turn a basic enemy to jade) and deals x<see cref="PetrifiedBonus"/> to an enemy
	/// already turned to jade.</item>
	/// <item>Right click: one glaive is thrown (<see cref="JadeGlaiveThrown"/>) up to <see cref="JadeGlaiveThrown.RangeTiles"/>
	/// tiles and comes back; it passes through the first enemy it meets going out and the first coming back (one hit each way),
	/// x<see cref="PetrifiedBonus"/> on jade. One out at a time; while it flies, the slashes are the other glaive's alone. The
	/// throw takes x<see cref="ThrowTimeMultiplier"/> a slash's time. Since 2026-11-24 (user: "increase the rotation speed of
	/// the throw ... (so it looks better like a fan spining) attack and the range a bit. it should cost 10 steam now"): 22
	/// tiles (18 before), spinning four times as fast with a blurred disc behind the blades, and
	/// <see cref="ThrowSteamCost"/> steam a throw.</item>
	/// </list>
	/// <para>Balance (D3; docs/balance/weapons.csv; T4, Coghaven's): anchor the Night's Edge (decompiled 1.4.4
	/// <c>Item.SetDefaults</c> 273: 40 damage, 25 use, 4.5 knockback): <see cref="Damage"/> every <see cref="UseTime"/> ticks at
	/// 12% crit, the jade curse on top. D2: the owner spawns the slash and the throw (<c>Shoot</c>); the slash's kind rides
	/// <c>ai[0]</c>, so every client draws the same X. Art: art/bosses/jadey/make_jadey_loot_art.py (the twin-crescent first
	/// version: previous/make_jadey_loot_art_2026-11-17.py).</para>
	/// </summary>
	public class JadeCursedGlaives : CogpunkItem, ISteamSkill
	{
		public const int Damage = 27;                       // user-set 2026-11-17 (24 before)
		public const int CritBonus = 8;                     // user-set 2026-11-17: 12% with the player's own 4%
		public const float PetrifiedBonus = 1.5f;           // user-set: +50% on an enemy turned to jade, slashes and throw (2026-11-17)
		public const int UseTime = 16;                      // "fast use time"
		public const float Knockback = 3.5f;
		public const float ThrowTimeMultiplier = 1.75f;
		/// <summary>The throw's steam (user-set 2026-11-24: "it should cost 10 steam now"): a steam skill
		/// (<see cref="ISteamSkill"/>), paid by a Mechanist weapon's rules (no tank: no throw and a hint; a short tank: an
		/// overheat), as the Sheriff's Revolver's burst is.</summary>
		public const int ThrowSteamCost = 10;

		public int SkillSteamCost => ThrowSteamCost;

		/// <summary>The alt use is the throw: its hits count its steam for the Spring Gloves.</summary>
		public int SteamForUse(Player player) => player.altFunctionUse != 0 ? player.GetModPlayer<SteamPlayer>().GetCost(ThrowSteamCost) : 0;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(JadeGlaiveThrown.RangeTiles,
			(int)System.Math.Round((PetrifiedBonus - 1f) * 100f), ThrowSteamCost);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
			ItemID.Sets.ItemsThatAllowRepeatedRightClick[Type] = true;
		}

		public override void SetDefaults() {
			Item.width = 70;                                     // the dropped item's box (2026-11-18: the sprite is 140 x 46)
			Item.height = 26;
			Item.DamageType = DamageClass.Melee;
			Item.damage = Damage;
			Item.crit = CritBonus;
			Item.knockBack = Knockback;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.noMelee = true;
			Item.noUseGraphic = true;
			Item.autoReuse = true;
			Item.shoot = ModContent.ProjectileType<JadeGlaiveSlash>();
			Item.shootSpeed = 1f;
			Item.UseSound = SoundID.Item1 with { Pitch = 0.25f, Volume = 0.8f };
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = ItemRarityID.Orange;
		}

		public override bool AltFunctionUse(Player player) => true;

		/// <summary>One glaive thrown at a time, and the throw's steam in the tank (the owner asks; the hint or the overheat when
		/// it can't pay).</summary>
		public override bool CanUseItem(Player player) {
			if (player.altFunctionUse != 2) {
				return true;
			}
			if (player.ownedProjectileCounts[ModContent.ProjectileType<JadeGlaiveThrown>()] >= 1) {
				return false;
			}
			return player.whoAmI != Main.myPlayer || player.GetModPlayer<SteamPlayer>().CanPayAttack(ThrowSteamCost);
		}

		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			SteamSkillTooltip.AddNoTankLine(Mod, tooltips, ThrowSteamCost);
		}

		public override float UseTimeMultiplier(Player player) => player.altFunctionUse == 2 ? ThrowTimeMultiplier : 1f;

		public override float UseAnimationMultiplier(Player player) => player.altFunctionUse == 2 ? ThrowTimeMultiplier : 1f;

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			if (player.altFunctionUse == 2) {
				Vector2 aim = velocity.SafeNormalize(new Vector2(player.direction, 0f));
				if (SafeSpawn.TryNewProjectile(source, player.MountedCenter, aim * JadeGlaiveThrown.ThrowSpeed, ModContent.ProjectileType<JadeGlaiveThrown>(),
						damage, knockback, out _, player.whoAmI)) {
					player.GetModPlayer<SteamPlayer>().Spend(ThrowSteamCost);   // CanUseItem checked it (Shoot runs on the owner)
					SoundEngine.PlaySound(SoundID.Item7 with { Pitch = 0.1f }, player.Center);
				}
				return false;
			}
			int kind = player.GetModPlayer<JadeGlavePlayer>().NextSlash(player.ownedProjectileCounts[ModContent.ProjectileType<JadeGlaiveThrown>()] > 0);
			SafeSpawn.TryNewProjectile(source, player.MountedCenter, Vector2.Zero, type, damage, knockback, out _, player.whoAmI, kind, player.itemAnimationMax);
			return false;
		}
	}

	/// <summary>Which glaive slashes next (the owner's; the choice rides the slash's synced <c>ai[0]</c>).</summary>
	public sealed class JadeGlavePlayer : ModPlayer
	{
		private int next;

		/// <summary>0: the front glaive ("\"), 1: the back one ("/"); only the front one while the back one is thrown.</summary>
		public int NextSlash(bool backThrown) {
			if (backThrown) {
				next = 1;
				return 0;
			}
			int kind = next;
			next = 1 - next;
			return kind;
		}
	}
}
