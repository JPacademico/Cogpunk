using Terraria.ModLoader;

namespace Cogpunk.Core.Templates
{
	// Abstract bases for all Cogpunk content. tModLoader skips abstract classes when autoloading.
	// Today they only add the missing-texture fallback; shared defaults and hooks for each content
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
