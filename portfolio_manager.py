import argparse
import json
import yaml
from eiten import Eiten
from argchecker import ArgChecker

def main():
    parser = argparse.ArgumentParser()
    
    # Add config file option
    parser.add_argument("--config", type=str, help="Path to config file (YAML or JSON)")
    parser.add_argument("--stocks", type=str, help="Path to stocks file (quick run)")
    
    # Keep existing args but make them optional
    commands = json.load(open("commands.json", "r"))
    for cmd in commands:
        parser.add_argument(cmd["comm"], type=eval(cmd["type"]), 
                           default=None, help=cmd["help"])
    
    args = parser.parse_args()
    
    # Load config file if provided
    if args.config:
        if args.config.endswith('.yaml') or args.config.endswith('.yml'):
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        else:
            with open(args.config, 'r') as f:
                config = json.load(f)
        
        # Override with command line arguments
        for key, value in vars(args).items():
            if value is not None:
                config[key] = value
        
        # Create new args object
        args = argparse.Namespace(**config)
    
    # Quick run with just stocks file
    elif args.stocks:
        args = argparse.Namespace(
            is_test=1,
            future_bars=90,
            data_granularity_minutes=3600,
            history_to_use="all",
            apply_noise_filtering=1,
            market_index="QQQ",
            only_long=1,
            eigen_portfolio_number=3,
            stocks_file_path=args.stocks,
            save_plot=True
        )
    
    ArgChecker(args)
    eiten = Eiten(args)
    eiten.run_strategies()

if __name__ == '__main__':
    main()