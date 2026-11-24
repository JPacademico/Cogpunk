using System.Collections.Concurrent;
using System.Reflection;
using Cogpunk.Core.Safety;
using Terraria.UI.Chat;

namespace Cogpunk.Core.Hooks
{
	/// <summary>
	/// Chat tags of our own (<c>[tag:...]</c> in chat, NPC dialogue and mouse text: vanilla parses them through
	/// <c>ChatManager.ParseMessage</c>, decompiled 1.4.4). Registering is vanilla's public <c>ChatManager.Register&lt;T&gt;</c>;
	/// vanilla has no way to remove one, so <see cref="Unregister"/> takes ours out of its private <c>_handlers</c> table by
	/// reflection when the mod unloads (the one reflection touch here, D0 rule 14: wrapped, logged once, and harmless if it
	/// fails: a leftover handler is only ever asked for our own tag).
	/// </summary>
	public static class ChatTagRegistry
	{
		public static void Register<T>(string tag) where T : ITagHandler, new() {
			try {
				ChatManager.Register<T>(tag);
			}
			catch (System.Exception e) {
				SafeLog.Warn("ChatTag.Register:" + tag, "Could not register the chat tag [{0}]: {1}", tag, e.Message);
			}
		}

		public static void Unregister(string tag) {
			try {
				FieldInfo field = typeof(ChatManager).GetField("_handlers", BindingFlags.NonPublic | BindingFlags.Static);
				if (field?.GetValue(null) is ConcurrentDictionary<string, ITagHandler> handlers) {
					handlers.TryRemove(tag.ToLower(), out _);
				}
			}
			catch (System.Exception e) {
				SafeLog.Warn("ChatTag.Unregister:" + tag, "Could not remove the chat tag [{0}]: {1}", tag, e.Message);
			}
		}
	}
}
