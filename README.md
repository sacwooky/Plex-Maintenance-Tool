# Plex Maintenance Tool

A Python-based utility for maintaining and managing your Plex Media Server libraries. This tool provides automated maintenance operations to help keep your Plex server organized and clean.

## Features

- **Label Management**: Clean up and organize labels across your libraries while preserving specified tags
- **Poster Reset**: Reset all posters to their default state or refresh metadata
- **Multi-Library Support**: Manage multiple Plex libraries from a single interface
- **Configurable Processing**: Adjust processing intensity based on your server's capabilities
- **Detailed Logging**: Track all operations with comprehensive error logging and summaries
- **Interactive Setup**: Easy-to-use setup wizard for initial configuration

## Prerequisites

- Python 3.7 or higher
- A Plex Media Server instance
- Plex authentication token
- Access to your Plex server's URL

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/plex-maintenance-tool.git
cd plex-maintenance-tool
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

On first run, the tool will launch a setup wizard that guides you through:
- Connecting to your Plex server
- Selecting libraries to manage
- Setting processing intensity
- Configuring label preservation

Your configuration is saved in `config.json` and can be modified later through the tool's interface.

### Getting Your Plex Token

To obtain your Plex authentication token:
1. Sign in to Plex web app
2. Navigate to any media item and open the XML toolkit (Three dots -> Get Info -> View XML)
3. Your "X-Plex-Token" will be visible in the URL

## Usage

1. Start the tool:
```bash
python pmt.py
```

2. Use the interactive menu to select:
   - Clean Up Labels: Remove unwanted labels while preserving specified ones
   - Reset Posters: Reset all posters to their defaults
   - Reconfigure Settings: Modify your configuration

## Processing Modes

- **Light**: 1 worker - Minimal server impact
- **Medium**: 2 workers - Balanced performance
- **Heavy**: 4 workers - Maximum performance, higher server load

## Logging

Operations are logged in the `logs` directory:
- `errors.log`: Detailed error messages
- `summary.log`: Operation summaries and statistics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Best Practices

- Start with light processing mode to assess impact on your server
- Regularly backup your Plex database before running maintenance operations
- Monitor the logs directory for operation results and any errors
- Test operations on a small library first

## Security Notes

- Keep your `config.json` secure as it contains your Plex token
- Don't share logs that might contain sensitive information
- Use HTTPS for remote Plex server connections

## Troubleshooting

Common issues and solutions:

1. Connection Failed
   - Verify Plex server URL is correct
   - Confirm Plex token is valid
   - Check server is running and accessible

2. Operation Timeout
   - Try reducing processing mode intensity
   - Check server resource usage
   - Verify network connectivity

3. Missing Libraries
   - Refresh Plex libraries
   - Check library permissions
   - Verify library exists in Plex

## License

[MIT License](LICENSE)

## Acknowledgments

- Built with [PlexAPI](https://github.com/pkkid/python-plexapi)
- Interactive prompts powered by [Inquirer](https://github.com/magmax/python-inquirer)

## Support

For issues and feature requests, please use the GitHub issues tracker.
