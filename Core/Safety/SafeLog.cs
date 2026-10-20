using System;
using System.Collections.Generic;
using log4net;

namespace Cogpunk.Core.Safety
{
	/// <summary>
	/// Rate-limited logging. A log call that fires every tick is a "console loop" (D0): it floods
	/// client.log/server.log, costs frame time and hides the real error. Every key is reported at most
	/// <see cref="MaxReportsPerKey"/> times per load, followed by a single "suppressed" line.
	/// Thread-safe, because world generation runs off the main thread.
	/// </summary>
	public static class SafeLog
	{
		public const int MaxReportsPerKey = 3;

		private static readonly Dictionary<string, int> reportCounts = new();
		private static readonly object gate = new();
		private static ILog logger;

		internal static void Init(ILog log) {
			logger = log;
		}

		internal static void Clear() {
			lock (gate) {
				reportCounts.Clear();
			}
			logger = null;
		}

		/// <summary>
		/// True while <paramref name="key"/> still has reports left. Build expensive messages only inside
		/// <c>if (SafeLog.ShouldReport(key))</c>, so repeated calls allocate nothing.
		/// </summary>
		public static bool ShouldReport(string key) {
			int count;
			lock (gate) {
				reportCounts.TryGetValue(key, out count);
				if (count > MaxReportsPerKey) {
					return false;
				}
				reportCounts[key] = count + 1;
			}
			if (count == MaxReportsPerKey) {
				logger?.Warn($"[{key}] repeated {MaxReportsPerKey}+ times; further reports suppressed until the mod reloads.");
				return false;
			}
			return true;
		}

		public static void Info(string key, string message) {
			if (ShouldReport(key)) {
				logger?.Info($"[{key}] {message}");
			}
		}

		public static void Warn(string key, string message) {
			if (ShouldReport(key)) {
				logger?.Warn($"[{key}] {message}");
			}
		}

		/// <summary>Formats only when the report is actually written, so suppressed calls allocate nothing.</summary>
		public static void Warn<T>(string key, string format, T arg) {
			if (ShouldReport(key)) {
				logger?.Warn($"[{key}] " + string.Format(format, arg));
			}
		}

		/// <summary>Formats only when the report is actually written, so suppressed calls allocate nothing.</summary>
		public static void Warn<T1, T2>(string key, string format, T1 arg1, T2 arg2) {
			if (ShouldReport(key)) {
				logger?.Warn($"[{key}] " + string.Format(format, arg1, arg2));
			}
		}

		public static void Error(string key, Exception exception) {
			if (ShouldReport(key)) {
				logger?.Error($"[{key}] {exception}");
			}
		}
	}
}
