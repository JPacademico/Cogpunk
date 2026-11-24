using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Mounts
{
	/// <summary>
	/// Missing Bones (Ossos Perdidos), the item that calls the mount of the same name (user, 2026-11-24: "reconstructed ...
	/// unlocks the crafting recipe for a new mount called "missing bones" a raptor skeleton that is fast and make the player imune
	/// to tar poisoning (a way to reach the fundamental stone under the pool)"): a raptor's skull strung on a tarred cord. Its
	/// recipe (my call: the bones and the tar of the Tar Tyrant, whose manual teaches it) is locked until the node "Reconstructed"
	/// (<see cref="ResearchNodes.Reconstructed"/>, <see cref="ResearchRecipes"/>). See <see cref="MissingBonesMount"/>.
	/// Art: art/research/make_missing_bones_art.py.
	/// </summary>
	public class MissingBones : CogpunkItem
	{
		public const int BoneCost = 30, TarCost = 10;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 26;
			Item.useTime = 20;
			Item.useAnimation = 20;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Orange;
			Item.UseSound = SoundID.NPCHit2 with { Pitch = -0.2f };   // dry bones clattering together
			Item.noMelee = true;
			Item.mountType = ModContent.MountType<MissingBonesMount>();
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.Bone, BoneCost)
				.AddIngredient<Junkyard.Items.CondensedTar>(TarCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}

	/// <summary>Riding Missing Bones: the mount stays while it lasts, and the rider can't catch the tar's plague
	/// (<see cref="Junkyard.Tar.TarPlague"/>: its own doc foresaw this, "a later item lets players dive by granting immunity the
	/// vanilla way"; vanilla clears the buff's immunities just before the buffs update, decompiled 1.4.4 <c>Player.Update</c>,
	/// and refuses an immune buff in <c>AddBuff</c>, so the pool's check that follows can't give it).</summary>
	public class MissingBonesBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoTimeDisplay[Type] = true;
			Main.buffNoSave[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			player.mount.SetMount(ModContent.MountType<MissingBonesMount>(), player);
			player.buffTime[buffIndex] = 10;
			int tar = ModContent.BuffType<Junkyard.Tar.TarPlague>();
			if (tar > 0 && tar < player.buffImmune.Length) {
				player.buffImmune[tar] = true;
			}
		}
	}
}
