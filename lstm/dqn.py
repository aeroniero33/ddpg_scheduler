import numpy as np
import gym

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam

from rl.agents.dqn import DQNAgent
from rl.policy import LinearAnnealedPolicy, EpsGreedyQPolicy
from rl.memory import EpisodeParameterMemory

from simulation import IoT_Simulation


def main(env_name, nb_steps):
    # Get the environment and extract the number of actions.
    #env = gym.make(env_name)
    env = IoT_Simulation()
    np.random.seed(123)
    env.seed(123)

    #nb_actions = env.action_space.n
    nb_actions = 6
    #input_shape = (1,) + env.observation_space.shape
    input_shape = env.observation_space.shape
    model = create_nn_model(input_shape, nb_actions)

    # Finally, we configure and compile our agent.
    memory = EpisodeParameterMemory(limit=2000, window_length=1)

    policy = LinearAnnealedPolicy(EpsGreedyQPolicy(), attr='eps', value_max=1444,
                                  value_min=0, value_test=600,
                                  nb_steps=1000000)

    agent = DQNAgent(model=model, nb_actions=nb_actions, policy=policy,
                     memory=memory, nb_steps_warmup=50000,
                     gamma=.99, target_model_update=10000,
                     train_interval=4, delta_clip=1.)
    print(f"Value: {policy.get_current_value()}")
    agent.compile(Adam(lr=.00001), metrics=['mae'])
    agent.fit(env, nb_steps=nb_steps, visualize=True, verbose=2)

    # After training is done, we save the best weights.
    agent.save_weights('dqn_{}_params.h5f'.format(env_name), overwrite=True)

    # Finally, evaluate the agent
    history = agent.test(env, nb_episodes=100, visualize=False)
    rewards = np.array(history.history['episode_reward'])
    print(("Test rewards (#episodes={}): mean={:>5.2f}, std={:>5.2f}, "
           "min={:>5.2f}, max={:>5.2f}")
          .format(len(rewards),
                  rewards.mean(),
                  rewards.std(),
                  rewards.min(),
                  rewards.max()))


def create_nn_model(input_shape, nb_actions):
    """
    Create a neural network model which maps the input to actions.

    Parameters
    ----------
    input_shape : tuple of int
    nb_actoins : int

    Returns
    -------
    model : keras Model object
    """
    model = Sequential()
    model.add(Flatten(input_shape=input_shape))
    model.add(Dense(32))
    model.add(Activation('relu'))
    model.add(Dense(64))
    model.add(Activation('relu'))
    model.add(Dense(64))
    model.add(Activation('relu'))
    model.add(Dense(512))
    model.add(Activation('relu'))
    model.add(Dense(nb_actions))
    model.add(Activation('linear'))
    print(model.summary())
    return model


def get_parser():
    """Get parser object."""
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--env",
                        dest="environment",
                        help="OpenAI Gym environment",
                        metavar="ENVIRONMENT",
                        default="CartPole-v0")
    parser.add_argument("--steps",
                        dest="steps",
                        default=10000,
                        type=int,
                        help="how many steps is the model trained?")
    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.environment, args.steps)