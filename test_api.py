from Bugfix_agent import BugFixAgent


def main():
    agent = BugFixAgent()
    repo = r"C:\Users\Ishan Khan\sample_repo"

    print("Indexing...")
    agent.index_repository(repo)

    print("Fixing bug...")
    result = agent.fix_bug(
        repo,
        "The divide function multiplies instead of dividing.",
    )

    print(result)


if __name__ == "__main__":
    main()
