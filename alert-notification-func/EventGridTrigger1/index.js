const { EmailClient } = require("@azure/communication-email");

module.exports = async function (context, eventGridEvent) {
    try {
        context.log("EVENT GRID FUNCTION TRIGGERED");

        const data = eventGridEvent.data || {};

        const recipient =
            typeof data.recipient === "string"
                ? data.recipient
                : data.recipient?.email || data.recipient?.address;
        const jobTitle = data.jobTitle || "New Job Match";
        const company = data.company || "Unknown Company";
        const jobId = data.jobId || "N/A";

        if (!recipient) {
            throw new Error("Recipient email is missing");
        }

        const connectionString =
            process.env.COMMUNICATION_SERVICES_CONNECTION_STRING;

        const senderAddress =
            process.env.EMAIL_SENDER_ADDRESS;

        if (!connectionString) {
            throw new Error("COMMUNICATION_SERVICES_CONNECTION_STRING is missing");
        }

        if (!senderAddress) {
            throw new Error("EMAIL_SENDER_ADDRESS is missing");
        }

        const emailClient = new EmailClient(connectionString);

        const message = {
            senderAddress,
            content: {
                subject: `New Job Match: ${jobTitle}`,
                plainText:
                    `A new job matching your preferences was found.\n\n` +
                    `Job: ${jobTitle}\n` +
                    `Company: ${company}\n` +
                    `Job ID: ${jobId}`,
                html: `
                    <h2>New Job Match</h2>
                    <p>A new job matching your preferences was found.</p>
                    <p>
                        <strong>Job:</strong> ${jobTitle}<br>
                        <strong>Company:</strong> ${company}<br>
                        <strong>Job ID:</strong> ${jobId}
                    </p>
                `
            },
            recipients: {
                to: [
                    {
                        address: recipient
                    }
                ]
            }
        };

        context.log(`Sending email to ${recipient}`);

        const poller = await emailClient.beginSend(message);
        const result = await poller.pollUntilDone();

        context.log(`Email status: ${result.status}`);
    } catch (error) {
        context.log.error("Notification failed:", error);
        throw error;
    }
};