using MagicalNuts.BackTest;

namespace MagicalNuts.Sample.CryptoBotSample
{
	public interface IStrategyProvider
	{
		IStrategy Strategy { get; }
		Controller Controller { get; }
	}
}
