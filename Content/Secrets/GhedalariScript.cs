using System.Text;
using Cogpunk.Content.Research;
using Terraria;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// The Ghedalari script (user, 2026-11-24: "rework so the runes (the Ghedalari language) are a custom created runic/symbolical
	/// language for our mod lore and the translation to make sense so players that are immersed on the lore can actualy learn
	/// the language"). Every <see cref="Word"/> has a rune (abstract strokes: what the Fundamental Stones and the Last Ghedalari
	/// show) and a pictogram (what a translation shows), both in <c>GhedalariGlyphs.png</c> (art/secrets/make_ghedalari_script_art.py:
	/// the runes on row 0, the pictograms on row 1; cells <see cref="CellW"/> x <see cref="CellH"/> on a <see cref="StrideX"/> x
	/// <see cref="StrideY"/> stride). The stones' sigils (fleur, sun, mountain, cross, wave) are the first five glyphs of
	/// <c>FundamentalRunes.png</c> and name the stones.
	/// <list type="bullet">
	/// <item><b>Translation</b> (the puzzle's first layer, user: "after unlocking the node and interacting with the stone again the
	/// symbols show are translated not to actual words but to more comprehensible symbols"): a stone's words show as pictograms to a
	/// player who has researched that stone's sigil node in the Mystery of the Past (<see cref="Translated"/>); a player knows a word
	/// once it is on a stone they have translated (<see cref="Knows"/>), which the Last Ghedalari's chat uses for its hover hints.</item>
	/// <item><b>What the stones say</b> (<see cref="Inscriptions"/>): the tar pit's only "..." (user); Westworld's
	/// rod, arrow, lake, bee: "a fishing rod then a arrow pointing to a lake + a bee (since the Ghedalari dont know "honey" and call
	/// it bee-water)": a fish caught from honey, a Honeyfin, given to it (<see cref="FundamentalStones"/>); the others only
	/// "stone, sleep" until the user gives their riddles.</item>
	/// <item><b>The Last Ghedalari's phrases</b> (<see cref="Phrases"/>, user: "phrases about his species with humour and some hints
	/// about the stones, but it should talk in Ghedalari symbols"), written as chat tags (<see cref="ChatTag"/>, drawn by
	/// <see cref="GhedalariTagHandler"/>).</item>
	/// </list>
	/// D1: the tables are built once; the tag strings are built when the NPC speaks (rarely), never per tick.
	/// </summary>
	public static class GhedalariScript
	{
		public enum Word : byte { Dot, Rod, Arrow, Lake, Bee, Ghedalari, One, Many, Not, You, Eat, Happy, Gold, Stone, Sleep, Sun }

		public const int WordCount = 16;
		public const int CellW = 18, CellH = 22, StrideX = 20, StrideY = 24;   // game px in GhedalariGlyphs.png
		public const int SigilW = 14, SigilH = 18, SigilStride = 16;            // FundamentalRunes.png
		public const string Sheet = "Cogpunk/Content/Secrets/GhedalariGlyphs";

		/// <summary>The words each stone shows after its sigil, by stone (its style).</summary>
		public static readonly Word[][] Inscriptions = {
			new[] { Word.Dot, Word.Dot, Word.Dot },                         // the tar pit: "..." (user-set)
			new[] { Word.Rod, Word.Arrow, Word.Lake, Word.Bee },           // Westworld: rod -> lake + bee (user-set)
			new[] { Word.Stone, Word.Sleep },                              // the ruins' stone: to come
			new[] { Word.Stone, Word.Sleep },
			new[] { Word.Stone, Word.Sleep },
		};

		/// <summary>The research node that translates stone <paramref name="stone"/> (its sigil in the Mystery of the Past).</summary>
		public static string SigilNode(int stone) => stone switch {
			FundamentalStones.TarPit => ResearchNodes.SigilFleur,
			FundamentalStones.Westworld => ResearchNodes.SigilSun,
			FundamentalStones.Ruins => ResearchNodes.SigilMountain,
			3 => ResearchNodes.SigilCross,
			4 => ResearchNodes.SigilWave,
			_ => null,
		};

		/// <summary>The player has researched the stone's sigil node: its words show as pictograms.</summary>
		public static bool Translated(Player player, int stone) {
			string node = SigilNode(stone);
			return node != null && player != null && player.GetModPlayer<ResearchPlayer>().Has(node);
		}

		/// <summary>The player has seen <paramref name="word"/> translated on a stone.</summary>
		public static bool Knows(Player player, Word word) {
			for (int k = 0; k < Inscriptions.Length; k++) {
				if (!Translated(player, k)) {
					continue;
				}
				foreach (Word w in Inscriptions[k]) {
					if (w == word) {
						return true;
					}
				}
			}
			return false;
		}

		// --- the Last Ghedalari's phrases: words, sigils (Sigil + the stone) and gaps -------------------------------------

		public const short Gap = -1;                    // a space between words (where a line may break)
		public const short Sigil = 100;                 // Sigil + k: stone k's sigil (its name)

		private static short W(Word w) => (short)w;

		/// <summary>
		/// His lines (my wording of the user's brief, in the script's own words):
		/// <list type="number">
		/// <item>"Ghedalari: one. Many: no." (the last of his kind)</item>
		/// <item>"You eat bee-water: happy." (honey, which his people never knew; bee-water is LAKE BEE, as Westworld's stone
		/// writes it)</item>
		/// <item>"Ghedalari eat gold: not happy." (he tried)</item>
		/// <item>"Stone, sleep. Stone, not eat." (don't)</item>
		/// <item>"Sun stone sleeps. You: rod, towards bee-water." (Westworld's stone wants a fish caught from honey)</item>
		/// <item>"Sun -> fleur -> mountain -> cross -> wave." (the order the stones must wake in)</item>
		/// <item>with the Witch Doctor: "Many you, towards one Ghedalari: happy."</item>
		/// <item>with the Dryad: "Stone, many suns. Ghedalari, one." (she and the stones are the only things as old as he)</item>
		/// </list>
		/// </summary>
		public static readonly short[][] Phrases = {
			new[] { W(Word.Ghedalari), W(Word.One), Gap, W(Word.Dot), Gap, W(Word.Many), W(Word.Not) },
			new[] { W(Word.You), Gap, W(Word.Eat), Gap, W(Word.Lake), W(Word.Bee), Gap, W(Word.Arrow), Gap, W(Word.Happy) },
			new[] { W(Word.Ghedalari), Gap, W(Word.Eat), Gap, W(Word.Gold), Gap, W(Word.Arrow), Gap, W(Word.Not), W(Word.Happy) },
			new[] { W(Word.Stone), Gap, W(Word.Sleep), Gap, W(Word.Dot), Gap, W(Word.Stone), Gap, W(Word.Not), W(Word.Eat) },
			new[] { (short)(Sigil + FundamentalStones.Westworld), W(Word.Stone), Gap, W(Word.Sleep), Gap, W(Word.Dot), Gap, W(Word.You),
				Gap, W(Word.Rod), Gap, W(Word.Arrow), Gap, W(Word.Lake), W(Word.Bee) },
			new[] { (short)(Sigil + FundamentalStones.Westworld), Gap, W(Word.Arrow), Gap, (short)(Sigil + FundamentalStones.TarPit), Gap,
				W(Word.Arrow), Gap, (short)(Sigil + FundamentalStones.Ruins), Gap, W(Word.Arrow), Gap, (short)(Sigil + 3), Gap,
				W(Word.Arrow), Gap, (short)(Sigil + 4) },
		};

		public static readonly short[] WitchDoctorPhrase = { W(Word.Many), W(Word.You), Gap, W(Word.Arrow), Gap, W(Word.One),
			W(Word.Ghedalari), Gap, W(Word.Happy) };

		public static readonly short[] DryadPhrase = { W(Word.Stone), Gap, W(Word.Many), W(Word.Sun), Gap, W(Word.Dot), Gap,
			W(Word.Ghedalari), Gap, W(Word.One) };

		/// <summary>A phrase as chat text: <c>[ghd:N]</c> runes, <c>[ghd/s:K]</c> sigils, spaces at the gaps.</summary>
		public static string ChatTag(short[] phrase) {
			StringBuilder sb = new(phrase.Length * 9);
			foreach (short t in phrase) {
				if (t == Gap) {
					sb.Append(' ');
				}
				else if (t >= Sigil) {
					sb.Append("[").Append(GhedalariTagHandler.Tag).Append("/s:").Append(t - Sigil).Append(']');
				}
				else {
					sb.Append("[").Append(GhedalariTagHandler.Tag).Append(':').Append(t).Append(']');
				}
			}
			return sb.ToString();
		}
	}
}
