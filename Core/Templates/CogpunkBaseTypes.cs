using Terraria.ModLoader;

namespace Cogpunk.Core.Templates
{
	// Abstract bases for all Cogpunk content. tModLoader skips abstract classes when autoloading.
	// They add the missing-texture fallback (and, for NPCs, Expert-first stats); shared defaults and hooks for each content
	// type go here later, so every item/NPC/tile picks them up without touching content files.
	// The resolved path is cached per instance: Texture is read again by draw code, and resolving
	// it each time would repeat the asset lookup.

	public abstract class CogpunkItem : ModItem
	{
		private string texture;
		public override string Texture => texture ??= TextureFallback.Resolve(base.Texture);
	}

	public abstract class CogpunkProjectile : ModProjectile
	{
		private string texture;
		public override string Texture => texture ??= TextureFallback.Resolve(base.Texture);
	}

	public abstract class CogpunkNPC : ModNPC
	{
		private string texture;
		public override string Texture => texture ??= TextureFallback.Resolve(base.Texture);

		private int expertLife, expertDamage;

		/// <summary>
		/// Call in <c>SetDefaults</c> with the <b>Expert</b> numbers (Cogpunk is balanced for Expert, see
		/// <see cref="ExpertStats"/>): Classic gets half the life and contact damage, Expert exactly these, Master 1.5x.
		/// </summary>
		protected void SetExpertStats(int life, int damage, int defense) {
			expertLife = life;
			expertDamage = damage;
			NPC.lifeMax = ExpertStats.Base(life);
			NPC.damage = ExpertStats.Base(damage);
			NPC.defense = defense;
		}

		/// <summary>Expert and Master only (vanilla's call): lands life and contact damage exactly on the Expert numbers
		/// given to <see cref="SetExpertStats"/>. Bosses with their own player scaling override this.</summary>
		public override void ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment) {
			if (expertLife > 0) {
				NPC.lifeMax = ExpertStats.Snap(NPC.lifeMax, expertLife);
			}
			if (expertDamage > 0) {
				NPC.damage = ExpertStats.Snap(NPC.damage, expertDamage);
			}
		}
	}

	public abstract class CogpunkTile : ModTile
	{
		private string texture;
		public override string Texture => texture ??= TextureFallback.Resolve(base.Texture);
	}

	public abstract class CogpunkWall : ModWall
	{
		private string texture;
		public override string Texture => texture ??= TextureFallback.Resolve(base.Texture);
	}

	public abstract class CogpunkBuff : ModBuff
	{
		private string texture;
		public override string Texture => texture ??= TextureFallback.Resolve(base.Texture);
	}
}
