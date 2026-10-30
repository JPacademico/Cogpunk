using System.Collections.Generic;
using Cogpunk.Content.Bosses.TrashTr0m;
using Cogpunk.Content.Jungle.NPCs;
using Cogpunk.Content.MechArmy.NPCs;
using Cogpunk.Core.Events;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy
{
	/// <summary>
	/// The Mech Army (user-set 2026-10-27): an invasion like the goblin army, run by <see cref="CogpunkInvasion"/> with
	/// vanilla's rules (size 80 + 40 per player with 5 Life Crystals, approach from a world edge, warnings, surface spawns
	/// near it at invasion rates, kill count, "defeated" and a downed flag, one invasion at a time).
	/// <list type="bullet">
	/// <item><b>When:</b> only once Trash-Tr0m has been defeated (<see cref="TrashTr0mSystem.Downed"/>), at dawn, with the
	/// goblin army's odds (decompiled <c>Main.UpdateTime_StartDay</c>): 1 in 3 until the Mech Army is first defeated, then
	/// 1 in 30, 1 in 60 in Hardmode. It rolls first and takes priority over vanilla's invasions that dawn
	/// (<see cref="InvasionDirector"/>). <c>/mecharmy</c> starts it for testing (<see cref="MechArmyCommand"/>).</item>
	/// <item><b>Roster</b> (<see cref="FillPool"/>; weights against the goblin army's mix, decompiled <c>NPC.SpawnNPC</c>:
	/// warrior 32%, archer 24%, peon 18%, thief 16%, sorcerer 11%): Rogue Mice-bots 40% (the swarm), Trappers 25% (the
	/// ranged hunters), Boombots 22% (kamikazes), Annoy-o-trons 13% and at most <see cref="MaxAnnoyOTrons"/> at once (the
	/// support). The <see cref="Jaeger"/> miniboss joins from <see cref="JaegerFrom"/> (50%, user-set) of the way through:
	/// one at a time, 1 spawn in <see cref="JaegerOdds"/> (the Goblin Summoner's odds), and it counts
	/// <see cref="JaegerKillValue"/> kills (the summoner's <c>InvasionSlotCount</c>).</item>
	/// <item><b>Hardmode</b> will add enemies and buffs (user, 2026-10-27, to be specified): <see cref="FillPool"/> and the
	/// enemies' stats are where they go.</item>
	/// </list>
	/// </summary>
	public sealed class MechArmyInvasion : CogpunkInvasion
	{
		public const float MiceWeight = 0.40f, TrapperWeight = 0.25f, BoombotWeight = 0.22f, AnnoyWeight = 0.13f;
		public const int MaxAnnoyOTrons = 2;
		public const float JaegerFrom = 0.5f;
		public const int JaegerOdds = 30;
		public const int JaegerKillValue = 10;
		public const int FirstOdds = 3, LaterOdds = 30, HardmodeOdds = 60;

		public override string FlagName => "DownedMechArmy";

		public override bool CanHappen => TrashTr0mSystem.Downed;

		public override int NaturalChanceDenominator => !Downed ? FirstOdds : (Main.hardMode ? HardmodeOdds : LaterOdds);

		public override string IconPath => "Cogpunk/Content/MechArmy/MechArmyIcon";

		public override Color BarColor => new Color(71, 145, 126) * 0.5f;     // verdigris: the Jaeger's paint

		public override int KillValue(int type) {
			if (type == ModContent.NPCType<Jaeger>()) {
				return JaegerKillValue;
			}
			return type == ModContent.NPCType<RogueMiceBot>() || type == ModContent.NPCType<Boombot>()
				|| type == ModContent.NPCType<AnnoyOTron>() || type == ModContent.NPCType<Trapper>() ? 1 : 0;
		}

		public override void FillPool(IDictionary<int, float> pool, NPCSpawnInfo spawnInfo) {
			pool[ModContent.NPCType<RogueMiceBot>()] = MiceWeight;
			pool[ModContent.NPCType<Trapper>()] = TrapperWeight;
			pool[ModContent.NPCType<Boombot>()] = BoombotWeight;
			float total = MiceWeight + TrapperWeight + BoombotWeight;
			int annoy = ModContent.NPCType<AnnoyOTron>();
			if (NPC.CountNPCS(annoy) < MaxAnnoyOTrons) {
				pool[annoy] = AnnoyWeight;
				total += AnnoyWeight;
			}
			int jaeger = ModContent.NPCType<Jaeger>();
			if (Progress >= JaegerFrom && !NPC.AnyNPCs(jaeger)) {
				pool[jaeger] = total / (JaegerOdds - 1);       // 1 spawn in JaegerOdds
			}
		}
	}

	/// <summary>The Mech Army's sounds (client-side; tModLoader loads the .wav files; nothing plays on a server).</summary>
	public static class MechArmySounds
	{
		/// <summary>The Annoy-o-tron's hi-lo siren, 0.96 s, played once a second; two at a time at most.</summary>
		public static readonly SoundStyle Alarm = new("Cogpunk/Assets/Sounds/MechArmy/AlarmSiren") {
			Volume = 0.5f,
			MaxInstances = 2,
			SoundLimitBehavior = SoundLimitBehavior.IgnoreNew,
		};

		/// <summary>The Boombot's proximity beep.</summary>
		public static readonly SoundStyle Beep = new("Cogpunk/Assets/Sounds/MechArmy/BoombotBeep") {
			Volume = 0.45f,
			MaxInstances = 4,
			SoundLimitBehavior = SoundLimitBehavior.ReplaceOldest,
		};
	}
}
