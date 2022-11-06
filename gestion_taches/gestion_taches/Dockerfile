FROM mcr.microsoft.com/dotnet/runtime:6.0 AS base
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY ["gestion_taches/gestion_taches.csproj", "gestion_taches/"]
RUN dotnet restore "gestion_taches/gestion_taches.csproj"
COPY . .
WORKDIR "/src/gestion_taches"
RUN dotnet build "gestion_taches.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "gestion_taches.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "gestion_taches.dll"]
