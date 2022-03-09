using MagicalNuts.Sample.CryptoBotSample;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddSingleton<IStrategyProvider, StrategyProvider<DonchianChannelBreakOut>>();

builder.Services.AddControllers();

var app = builder.Build();

// Configure the HTTP request pipeline.

app.UseAuthorization();

app.MapControllers();

app.Run();
