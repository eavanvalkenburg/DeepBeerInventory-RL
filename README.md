
# Setup

Ideally run this on a Github codespaces environment, but you can also run this locally.

To run this for Bonsai
Create a .env file in the root with the following contents:
```
SIM_WORKSPACE=<workspace id>
SIM_ACCESS_KEY=<key from serice>
```

Then run:

`pip install -r requirements.txt`

Finally:

`python main.py --config-setup`

To run manually (with you as a agent), run:

`python manual.py`
(exit by using ctrl+c)

## Known issues:
- Not 100% sure everything is correct.
- Bonsai tends to run away with a large number of orders, that is why the action is now capped at 20.
- The potential is there to use the same code with more then 4 agents, but Bonsai cannot deal with that in the same sim, so that would need a seperate `beergame.json` definition.
- The same with multiple agents trained by Bonsai.

### Disclaimer
This was created loosely based on the code from the forked repo, the old code is partly present in the old folder, but it is easier to just look at the original repo since some files were changed.
