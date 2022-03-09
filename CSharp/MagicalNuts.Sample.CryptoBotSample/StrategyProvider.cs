using MagicalNuts.BackTest;

namespace MagicalNuts.Sample.CryptoBotSample
{
	public class StrategyProvider<T> : IStrategyProvider where T : IStrategy, new()
	{
		private IStrategy? _Strategy = null;
		private Controller? _Controller = null;

		public IStrategy? Strategy => _Strategy;
		public Controller? Controller => _Controller;

		public StrategyProvider()
		{
			_Strategy = new T();
			_Strategy.SetUpAsync().ConfigureAwait(false);
			_Controller = new Controller();
		}
	}
}
