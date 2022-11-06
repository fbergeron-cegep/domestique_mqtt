// See https://aka.ms/new-console-template for more information

using System.Text.Json;
using MQTTnet;
using MQTTnet.Client;

namespace gestion_taches
{
    class Gestion
    {
        private static void Main()
        {
            Gestion gestion = new();
            gestion.Lancer();
        }

        private readonly IMqttClient _client;
        private readonly MqttFactory _mqttFactory;

        private Gestion()
        {
            _mqttFactory = new MqttFactory();
            _client = _mqttFactory.CreateMqttClient();
        }

        private void Lancer()
        {
            Task.Run(async () =>
            {
                await Connect_Client();
                await Subscribe_Topic();
                _client.ApplicationMessageReceivedAsync += (msg =>
                    Recevoir_Message(msg.ApplicationMessage));
            });

            while (true)
            {
                Console.ReadLine();
                Thread.Sleep(1000);
            }
        }

        private async Task Connect_Client()
        {
            var mqttClientOptions = new MqttClientOptionsBuilder().WithTcpServer("127.0.0.1").Build();
            await _client.ConnectAsync(mqttClientOptions, CancellationToken.None);

            Console.WriteLine("The MQTT client is connected.");
        }
        
        private async Task Subscribe_Topic()
        {
            var mqttSubscribeOptions = _mqttFactory.CreateSubscribeOptionsBuilder()
                .WithTopicFilter(
                    f =>
                    {
                        f.WithTopic("taches/#");
                    })
                .Build();

            await _client.SubscribeAsync(mqttSubscribeOptions, CancellationToken.None);
            Console.WriteLine("MQTT client subscribed to topic.");

        }

        private async Task Recevoir_Message(MqttApplicationMessage msg)
        {
            var topic = msg.Topic;
            var contenu = System.Text.Encoding.Default.GetString(msg.Payload);
            TachesData? data = JsonSerializer.Deserialize<TachesData>(contenu);

            var hierarchie = topic.Split('/');
            if (hierarchie.Length == 2) // C'est donc un nouveau sujet
            {
                Console.WriteLine("Débuter la tâche " + data!.nom_tache);
                Console.ReadLine();

                data.progres = "Debutee";

                var str = JsonSerializer.Serialize(data);
                await _client.PublishAsync(new MqttApplicationMessageBuilder()
                    .WithTopic(topic + "/etat")
                    .WithPayload(str)
                    .Build());
                
                Console.WriteLine("Terminer la tâche " + data.nom_tache);
                Console.ReadLine();
                
                data.progres = "Terminee";

                str = JsonSerializer.Serialize(data);
                await _client.PublishAsync(new MqttApplicationMessageBuilder()
                    .WithTopic(topic + "/etat")
                    .WithPayload(str)
                    .Build());
            }
        }
    }
}