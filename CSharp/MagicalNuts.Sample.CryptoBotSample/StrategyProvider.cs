using MagicalNuts.BackTest;

namespace MagicalNuts.Sample.CryptoBotSample
{
	public class StrategyProvider<T> : IStrategyProvider where T : class, IStrategy, new()
	{
		private T _Strategy = null;
		public IStrategy Strategy => _Strategy;

		public StrategyProvider()
		{
			_Strategy = new T();
			_Strategy.SetUpAsync().ConfigureAwait(false);
		}
	}
}
