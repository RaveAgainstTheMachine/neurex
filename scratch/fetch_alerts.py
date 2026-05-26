import subprocess
import json

def main():
    try:
        # Run gh command without GITHUB_TOKEN
        cmd = ["env", "-u", "GITHUB_TOKEN", "gh", "api", "repos/RaveAgainstTheMachine/neurex/code-scanning/alerts?state=open", "--paginate"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        alerts = json.loads(res.stdout)
        
        print(f"Total open alerts: {len(alerts)}")
        print("\n| Number | Rule | Severity | Path | Line | Message |")
        print("| --- | --- | --- | --- | --- | --- |")
        for alert in sorted(alerts, key=lambda x: x['number']):
            num = alert['number']
            rule = alert['rule']['id']
            sev = alert['rule'].get('security_severity_level', 'N/A')
            inst = alert.get('most_recent_instance', {})
            path = inst.get('location', {}).get('path', 'unknown')
            line = inst.get('location', {}).get('start_line', 'unknown')
            msg = inst.get('message', {}).get('text', '').replace('\n', ' ')
            print(f"| {num} | {rule} | {sev} | {path} | {line} | {msg} |")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
