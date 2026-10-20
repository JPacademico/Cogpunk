using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Templates
{
	/// <summary>
	/// Missing art must never stop the mod from loading (D0). When a content type's texture is missing,
	/// this returns the shared placeholder instead and logs one warning per texture, so work-in-progress
	/// content stays testable and the gap is visible in game and in the log.
	/// </summary>
	public static class TextureFallback
	{
		public const string Placeholder = "Cogpunk/Assets/Textures/Placeholder";

		public static string Resolve(string texture) {
			// HasAsset is always false on a dedicated server (no textures load there), so keep the real path.
			if (Main.dedServ || ModContent.HasAsset(texture)) {
				return texture;
			}
			SafeLog.Warn("Texture.Missing:" + texture, "Missing texture '{0}'; using the placeholder.", texture);
			return Placeholder;
		}
	}
}
