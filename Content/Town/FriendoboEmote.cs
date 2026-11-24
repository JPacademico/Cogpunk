using Cogpunk.Core.Templates;
using Terraria.GameContent.UI;
using Terraria.ModLoader;

namespace Cogpunk.Content.Town
{
	/// <summary>
	/// The Last Ghedalari's face emote (the Friendo-bot's until 2026-11-24; vanilla's townsfolk detail): the bubble other town NPCs show when
	/// they talk about him (<c>NPCID.Sets.FaceEmote</c>, ExampleMod 1.4.4's ExamplePerson), and his entry in the emote menu's
	/// Town category. The texture is two frames side by side in vanilla's 34x28 cell (decompiled <c>EmoteBubble.Draw</c>: a
	/// mod emote is <c>Frame(2, 1, frame)</c>): his head, then his head blinking. D0: a missing texture falls back
	/// (<see cref="TextureFallback"/>).
	/// </summary>
	public class FriendoboEmote : ModEmoteBubble
	{
		private string texture;

		public override string Texture => texture ??= TextureFallback.Resolve(base.Texture);

		public override void SetStaticDefaults() {
			AddToCategory(EmoteID.Category.Town);
		}
	}
}
