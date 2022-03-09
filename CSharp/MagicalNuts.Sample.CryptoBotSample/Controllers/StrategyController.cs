using MagicalNuts.BackTest;
using Microsoft.AspNetCore.Mvc;

namespace MagicalNuts.Sample.CryptoBotSample.Controllers
{
	[ApiController]
	[Route("[controller]")]
	public class StrategyController : Microsoft.AspNetCore.Mvc.Controller
	{
		[HttpPost]
		public ActionResult Post([FromServices] IStrategyProvider strategyProvider, [FromBody] string data)
		{
			BackTestStatus state = Utf8Json.JsonSerializer.Deserialize<BackTestStatus>(data);
			strategyProvider.Strategy.GetOrders(state, state.Orders);
			return Ok(state.Orders);
		}
	}
}
