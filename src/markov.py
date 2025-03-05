import numpy as np
import src.midi_utils as midi_utils

class MarkovChain:
    def __init__(self):
        """
        Initializes the Markov Chain with an empty states dictionary and transition matrix.
        """
        self.states = {}  # Maps state values to unique integer IDs
        self.transition_matrix = None
        self.state_count = 0 #The current count for states
        self.state_frequencies = {} #store how often each state is found.
    
    def create_state_dictionary(self, states):
        """Creates a dictionary that maps each state value (a tuple of (note, duration)) to a unique integer.

        Args:
            states (list): A list of states (e.g. note values).
        """
        for state in states:
            if state not in self.states:
                self.states[state] = self.state_count
                self.state_count += 1
                self.state_frequencies[state] = 0 #Set to zero, and increment in the next method

    def create_transition_matrix(self, states, k=1):
      """Creates the transition probability matrix based on the input states.

      Args:
          states (list): A list of states, where a state is a tuple of (note, duration).
          k (int): Additive smoothing factor.
      """
      num_states = len(self.states)
      self.transition_matrix = np.zeros((num_states, num_states))

      #Create the transition matrix from the state data.
      for i in range(len(states) - 1):
        current_state = states[i]
        next_state = states[i+1]
        current_state_id = self.states[current_state]
        next_state_id = self.states[next_state]
        self.transition_matrix[current_state_id, next_state_id] += 1 #increment the number of times a particular transition occurs
        self.state_frequencies[current_state] +=1 #increment frequency

      #convert the transition matrix to probabilities
      for row in range(num_states):
        row_sum = np.sum(self.transition_matrix[row])
        if row_sum > 0:
          self.transition_matrix[row] = (self.transition_matrix[row] + k) / (row_sum + k * num_states)
          
    def generate_sequence(self, length, start_state = None):
      """Generates a sequence of states based on the trained transition matrix.

      Args:
        length (int): The length of the sequence to generate
        start_state (tuple, optional): The starting state of the generation. If not provided, a random state will be selected.

      Returns:
        list: A list of states representing the generated sequence
      """
      if self.transition_matrix is None:
        raise ValueError("Transition matrix has not been created. Call create_transition_matrix first.")
      
      states_list = list(self.states.keys())
      
      if start_state is None:
        rand_id = np.random.choice(len(states_list))
        current_state = states_list[rand_id]
      else:
          current_state = start_state

      generated_sequence = []
      generated_sequence.append(current_state)
      for _ in range(length-1):
        current_state_id = self.states[current_state]
        probabilities = self.transition_matrix[current_state_id]
        
        # Check if the state exists in matrix
        if np.sum(probabilities) == 0: #If there are no transition probabilities for this state, then just chose a random one.
          #Normalize frequencies
          total_frequency = sum(self.state_frequencies.values())
          normalized_frequencies = [self.state_frequencies[state] / total_frequency for state in states_list]

          next_state_id = np.random.choice(len(states_list), p = normalized_frequencies)
          next_state = states_list[next_state_id]
        else:
          next_state_id = np.random.choice(len(states_list), p = probabilities)
          next_state = states_list[next_state_id]
        generated_sequence.append(next_state)
        current_state = next_state

      return generated_sequence

    def generate_midi_file(self, generated_sequence, filename="generated_solo.mid", tempo=120):
        """Generates a MIDI file from a sequence of states.

        Args:
            generated_sequence (list): A list of states (note, duration tuples).
            filename (str): The name of the output MIDI file.
            tempo (int): The tempo of the generated MIDI file (in BPM).
        """
        midi_utils.create_midi_file(generated_sequence, filename, tempo)