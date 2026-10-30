using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy
{
	/// <summary>
	/// <c>/mecharmy start | stop | win | status</c>: a testing tool for the Mech Army, whose natural start is a dawn roll.
	/// Singleplayer, or the dedicated server's console (in multiplayer a chat command would let any player start an
	/// invasion). <c>start</c> ignores the Trash-Tr0m gate, the dawn and the 5 Life Crystals (sized for at least one
	/// player); <c>win</c> finishes it as if the last enemy died (the "defeated" message and the downed flag).
	/// </summary>
	public sealed class MechArmyCommand : ModCommand
	{
		public override CommandType Type => CommandType.World | CommandType.Console;

		public override string Command => "mecharmy";

		public override string Usage => "/mecharmy start | stop | win | status";

		public override string Description => Text("Description");

		private static string Text(string key, params object[] args) => Language.GetTextValue("Mods.Cogpunk.Events.Command." + key, args);

		public override void Action(CommandCaller caller, string input, string[] args) {
			if (Main.netMode == NetmodeID.Server && caller.CommandType != CommandType.Console) {
				caller.Reply(Text("ConsoleOnly"), Color.OrangeRed);
				return;
			}
			MechArmyInvasion army = ModContent.GetInstance<MechArmyInvasion>();
			string verb = args.Length > 0 ? args[0].ToLowerInvariant() : "status";
			switch (verb) {
				case "start":
					caller.Reply(army.TryStart(force: true) ? Text("Started") : Text("CantStart"), Color.LightGreen);
					break;
				case "stop":
					if (army.Active) {
						army.End(won: false);
						caller.Reply(Text("Stopped"), Color.LightGreen);
					}
					else {
						caller.Reply(Text("NotRunning"), Color.OrangeRed);
					}
					break;
				case "win":
					if (army.Active) {
						army.Credit(army.Size);
						caller.Reply(Text("Won"), Color.LightGreen);
					}
					else {
						caller.Reply(Text("NotRunning"), Color.OrangeRed);
					}
					break;
				default:
					caller.Reply(army.Active ? Text("Status", army.Size, army.SizeStart, (int)(army.Progress * 100f)) : Text("NotRunning"), Color.LightGreen);
					break;
			}
		}
	}
}
