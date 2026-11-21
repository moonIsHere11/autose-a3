# Hidden acceptance tests

Kept outside the fork, so agents never see them. Run against a PR branch of the fork:

    git -C <fork> checkout autose/issue-<n> && cd <fork> && python -m pytest -q -o addopts= <this dir>/test_<I>.py

I1-I4 reuse the A2 hidden tests for the same behaviour (round1 T1/T2, round2 T1/T2); I5 is new.
